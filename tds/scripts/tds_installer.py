# Copyright 2016 Ifwe Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Daemon to do installations on servers.
Interacts with Zookeeper to get lock for grabbing queued deployments from DB.
When it grabs the lock, it calls self.app.run().
self.app is passed in during initialization and should be of type Installer,
from tds.apps.installer.
"""

import logging
import os
import os.path
import socket
import signal
import sys
import time
import traceback

from datetime import datetime, timedelta
from kazoo.client import KazooClient, KazooState
from kazoo.exceptions import CancelledError, ConnectionClosedError, LockTimeout
from kazoo.retry import KazooRetry

import tagopsdb
import tds.apps
import tds.exceptions
import tds.model
import tds.utils.processes

log = logging.getLogger('tds_installer')


class TDSInstallerDaemon:
    """Daemon to manage updating the deploy repository with new packages."""

    def __init__(self, app, *args, **kwargs):
        self._should_stop = False
        # ongoing_processes is a dict with deployment ID keys and values:
        # (subprocess_popen_instance, start_time)
        self.ongoing_processes = dict()
        self.threshold = kwargs.pop('threshold') if 'threshold' in kwargs \
            else timedelta(minutes=30)
        self.app = app
        self.heartbeat_time = datetime.now()
        self.has_lock = False
        self.lock = None

    def should_stop(self):
        return self._should_stop

    def sigterm_handler(self, signum, frame):
        """
        Shut down the daemon.
        """
        log.fatal('Received SIGTERM. Beginning shutdown...')
        self._should_stop = True
        if self.lock is not None:
            self.release_lock()

        if self.zoo is not None:
            self.zoo.stop()

    def main(self):
        """
        Read configuration file and get relevant information, then try
        to process queued deployments if single system or
        zookeeper leader in multi-system configuration.
        """
        self.exit_timeout = timedelta(
            seconds=self.app.config.get('exit_timeout', 160)
        )
        self.deploy_exit_timeout = timedelta(
            seconds=self.app.config.get('deploy_exit_timeout', 5)
        )
        zookeeper_config = self.app.config.get('zookeeper', None)

        if zookeeper_config is not None:
            self.lock = self.create_zoo(zookeeper_config)
            self.zk_run = self.lock_run
        else:
            self.zk_run = lambda f, *a, **k: f(*a, **k)

        while not self.should_stop():
            try:
                self.zk_run(self.handle_incoming_deployments)
            except ConnectionClosedError, TimeoutError:
                if not self.should_stop():
                    # Ignore errors raised by kazoo when it is having
                    # connection trouble; we're shutting down anyway.
                    raise

            self.clean_up_processes(wait=self.should_stop())
            time.sleep(0.1)     # Increase probability of other daemons running

        self.clean_up_processes(wait=True)
        self.zoo.close();
        log.info("Stopped.")

    def handle_incoming_deployments(self):
        """Look for files in 'incoming' directory and handle them."""
        tagopsdb.Session.close()
        deployment = self.app.find_deployment()

        # Heartbeat test to see if daemon is 'stuck'
        if (datetime.now() - self.heartbeat_time).seconds >= 900:
            self.heartbeat_time = datetime.now()
            log.info('HEARTBEAT - Deployment search result: %r', deployment)
            log.info("There {verb} {num_proc} ongoing process{mult}.".format(
                verb='is' if len(self.ongoing_processes) == 1 else 'are',
                num_proc=len(self.ongoing_processes),
                mult='' if len(self.ongoing_processes) == 1 else 'es',
            ))

        if deployment is None:
            return

        log.info('Found deployment with ID %s', deployment.id)
        deployment.status = 'inprogress'
        tagopsdb.Session.commit()
        installer_file_path = os.path.abspath(tds.apps.installer.__file__)
        if installer_file_path.endswith('.pyc'):
            installer_file_path = installer_file_path[:-1]
        try:
            deployment_process = tds.utils.processes.start_process([
                sys.executable,
                installer_file_path,
                deployment.id,
            ])
        except tds.exceptions.RunProcessError as exc:
            log.error('Exception: %r', exc.stderr)
        else:
            self.ongoing_processes[deployment.id] = (
                deployment_process, datetime.now()
            )

    def clean_up_processes(self, wait=False):
        """
        Check processes that have finished, terminate stalled processes, and
        reap all such processes.

        If wait is true, then do not exit until done (or timed out).
        """
        cleanup_start = datetime.now()
        terminated = {}
        killed = {}
        while True:
            now = datetime.now()
            for dep_id in self.ongoing_processes.keys():
                (proc, process_start) = self.ongoing_processes[dep_id];
                term_time = process_start + self.threshold
                if wait:
                    # If we're waiting for all processes here, then we probably
                    # need to kill this process earlier than its normal timeout.
                    term_time = min(
                        term_time,
                        # Give a 2-second fudge factor to allow reaping killed
                        # processes.
                        cleanup_start + self.exit_timeout - \
                            self.deploy_exit_timeout - timedelta(seconds=2)
                    )

                # 1. Kill terminated processes that should have exited by now.
                if proc in terminated and proc not in killed:
                    kill_time = terminated[proc] + self.deploy_exit_timeout
                    if now >= kill_time:
                        log.warning('Killing deployment ID %d.' % (dep_id))
                        proc.kill()
                        killed[proc] = now

                # 2. Terminate processes that have timed out.
                if now >= term_time and proc not in terminated:
                    log.warning('Terminating deployment ID %d.' % (dep_id))
                    proc.terminate()
                    terminated[proc] = now

                # 3. Check for processes that have exited and verify status.
                if self.waitproc(dep_id=dep_id, proc=proc):
                    dep = self.app.get_deployment(dep_id=dep_id)
                    self.app._refresh(dep)
                    log.debug(
                        'Deployment ID %d finished, status: %s.' % \
                            (dep_id, dep.status)
                    )

                    if dep.status not in ('complete', 'failed', 'stopped'):
                        # If it finished with a non-finished status, then
                        # something is wrong.
                        log.debug(
                            'Deployment ID %d forcing status to "failed".' % \
                                (dep_id)
                        )
                        # Note: this only sets the top-level deployments table
                        # entry to 'failed'; if the child process crashes or is
                        # killed, then the host_deployments and app_deployments
                        # entries will remain 'inprogress'. This is probably a
                        # deficiency here, but on the other hand, code
                        # elsewhere needs to be able to handle that situation
                        # anyway, should e.g. the entire host crash.
                        dep.status = 'failed'
                        self.app.commit_session()

                    del self.ongoing_processes[dep_id]

                    if proc in terminated:
                        del(terminated[proc])

                    if proc in killed:
                        del(killed[proc])

            # If we signalled any processes, then we generally want to keep
            # looping in order to not lose track of them. Only give up if we
            # are waiting on processes prior to exit anyway.
            busy = terminated or killed
            if wait:
                busy = busy or self.ongoing_processes

            give_up_time = cleanup_start + self.exit_timeout
            give_up = wait and now >= give_up_time

            if not busy or give_up:
                break

            time_left = give_up_time - now
            seconds_left = time_left.total_seconds()
            log.debug('Waiting %.1fs for children to finish.' % (seconds_left))
            # Old python does not provide timeouts for Popen methods.
            time.sleep(1)

    def create_zoo(self, zoo_config):
        """
        Create and return a new zoo.
        """
        hostname = socket.gethostname()

        # Set up our own KazooRetry classes in order to override default
        # parameters.
        command_retry = KazooRetry(
            # Old default is 3600; modern default is 60; we should be ok at 10.
            max_delay=10,
            # callback
            interrupt=self.should_stop,
        )
        connection_retry = KazooRetry(
            max_delay=10,
            # Retry forever (unless interrupted).
            max_tries=-1,
            interrupt=self.should_stop,
        )
        kzlog = log.getChild('kazoo')
        # debug is too verbose
        kzlog.setLevel(logging.INFO)
        self.zoo = KazooClient(
            hosts=','.join(zoo_config),
            # This sets the timeout on connections (and reconnections).
            timeout=3,
            connection_retry=connection_retry,
            command_retry=command_retry,
            logger=kzlog,
        )
        def state_listener(state):
            if not self.should_stop():
                if state == KazooState.CONNECTED:
                    log.info("Connected to ZooKeeper.")
                else:
                    if state == KazooState.SUSPENDED:
                        log.warning("ZooKeeper connection suspended.")
                    elif state == KazooState.LOST:
                        log.warning("ZooKeeper connection lost.")
                    else:
                        log.error("Unrecognized ZooKeeper state: %s" % (state))

                    # Trust in KazooClient to reconnect as needed, but release
                    # the lock, since it is probably invalid.
                    self.release_lock()

        self.zoo.add_listener(state_listener)
        self.zoo.start()
        return self.zoo.Lock('/tdsinstaller', hostname)

    def lock_run(self, func, *args, **kwargs):
        """
        Run the specified function, with the specified arguments, under a
        zookeeper lock. This will block until the lock is acquired or
        shutdown is initiated. Once done, the lock is not released, such that
        it may be re-used by subsequent runs. Lock release is handled
        elsewhere:
        1. During shutdown.
        2. When there is zookeeper connection trouble, which likely just
           updates client state, since zookeeper will automatically remove the
           lock when the client disconnects.
        """
        while not self.has_lock and not self.should_stop():
            try:
                # If no timeout is specified here, then kazoo will block on a
                # threading wait, which blocks the signal handler (at least on
                # python < 3.3).
                # If any timeout is specified, then kazoo will run an internal
                # check-sleep loop which does not block the signal handler. Do
                # not specify too low a timeout or else there will be a high
                # turnover of ephemeral zookeeper nodes, leading to overflow of
                # the (apparently) signed 32-bit int counter on the parent node.
                # A timeout of 60 should give us a zookeer node lifetime of
                # 4085 years.
                self.has_lock = self.lock.acquire(timeout=60)
            except CancelledError:
                log.debug("ZooKeeper lock acquisition cancelled")
            except LockTimeout:
                pass

            if self.has_lock:
                log.debug("Acquired ZooKeeper lock")

        # Once execution reaches this point, then we either got a lock, so run
        # the supplied function, or we are in shutdown (see loop conditions
        # above).
        if self.has_lock:
            func(*args, **kwargs)
        elif self.should_stop():
            log.debug("Aborted acquiring ZooKeeper lock due to shutdown")

    def release_lock(self):
        """
        Release any acquired locks and cancel any pending ones.
        """
        if self.has_lock:
            self.lock.release()
            self.has_lock = False

        if self.lock is not None:
            # This is idempotent; no need to set self.lock to None.
            self.lock.cancel()

    def run(self):
        """A wrapper for the main process to ensure any unhandled
           exceptions are logged before the daemon exits.
        """
        try:
            self.main()
        except Exception as exc:
            msg = "Unhandled exception: %r.  Daemon exiting." % exc
            msg += '\n' + traceback.format_exc()
            log.error(msg)
            sys.exit(1)

    def waitproc(self, dep_id, proc):
        """
        Do a nonblocking waitpid() on the PID of the supplied process. Check
        exit status and log information. Return True if the process has exited
        and False if not.
        """
        (pid, status) = os.waitpid(proc.pid, os.WNOHANG)
        if pid == proc.pid:
            # child exited
            # check exit status for logging
            log.debug('Deployment ID %d raw exit status: 0x%04X' % (dep_id, status))
            if os.WIFEXITED(status):
                exit_status = os.WEXITSTATUS(status)
                if exit_status == 0:
                    log.debug('Deployment ID %d exited successfully.' % (dep_id))
                else:
                    log.warning(
                        'Deployment ID %d exited with error status %d' % \
                            (dep_id, exit_status)
                    )
            elif os.WIFSIGNALED(status):
                log.warning(
                    'Deployment ID %d exited from signal %d' % \
                        (dep_id, os.WTERMSIG(status))
                )
            else:
                log.warning(
                    'Deployment ID %d exited for unknown reason' % (dep_id)
                )

            return True

        elif pid == 0:
            return False

        # should not happen
        log.error(
            'Deployment ID: %d unexpected waitpid; expected %d, got %d.' % \
                (dep_id, proc.pid, pid)
            )
        # don't trust further execution
        sys.exit(2)

def daemon_main():
    """Prepare logging then initialize daemon."""
    logfile = '/var/log/tds_installer.log'

    # 'logger' set at top of program
    rootlog = logging.getLogger('')
    rootlog.setLevel(logging.DEBUG)
    handler = logging.FileHandler(logfile, 'a')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s",
                                  "%b %e %H:%M:%S")
    handler.setFormatter(formatter)
    rootlog.addHandler(handler)
    logging.getLogger('kazoo').propagate = False

    app = tds.apps.Installer(dict(
        user_level='admin',
    ))

    daemon = TDSInstallerDaemon(app)

    signal.signal(signal.SIGTERM, daemon.sigterm_handler)

    daemon.run()

if __name__ == '__main__':
    daemon_main()
