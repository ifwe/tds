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
import os.path
import socket
import signal
import sys
import time
import traceback

from datetime import datetime, timedelta

from kazoo.client import KazooClient, KazooState

import tagopsdb
import tds.apps
import tds.exceptions
import tds.model
import tds.utils.processes

log = logging.getLogger('tds_installer')


class TDSInstallerDaemon:
    """Daemon to manage updating the deploy repository with new packages."""

    should_stop = False
    election = None

    def __init__(self, app, *args, **kwargs):
        # ongoing_processes is a dict with deployment ID keys and values:
        # (subprocess_popen_instance, start_time)
        self.ongoing_processes = dict()
        self.threshold = kwargs.pop('threshold') if 'threshold' in kwargs \
            else timedelta(minutes=30)
        self.app = app
        self.heartbeat_time = datetime.now()

    def sigterm_handler(self, signum, frame):
        """
        Shut down the daemon.
        """
        log.fatal('Received SIGTERM. Beginning shutdown...')
        if self.election is not None:
            self.election.cancel()
            self.election = None

        self.should_stop = True

    def main(self):
        """
        Read configuration file and get relevant information, then try
        to process queued deployments if single system or
        zookeeper leader in multi-system configuration.
        """
        self.exit_timeout = timedelta(
            seconds=self.app.config.get('exit_timeout', 160)
        )
        zookeeper_config = self.app.config.get('zookeeper', None)

        if zookeeper_config is not None:
            self.election = self.create_zoo(zookeeper_config)
            self.zk_run = self.election.run
        else:
            self.zk_run = lambda f, *a, **k: f(*a, **k)

        while not self.should_stop:
            self.zk_run(self.handle_incoming_deployments)
            self.clean_up_processes(wait=self.should_stop)
            time.sleep(0.1)     # Increase probability of other daemons running

        self.clean_up_processes(wait=True)
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
        Join processes that have finished and terminate stalled processes.

        If wait is true, then loop until the configured timeout.
        """
        start = datetime.now()

        to_delete = list()

        # No do/while in python. :(
        while True:
            # Remove entries for all done subprocesses
            for dep_id in self.ongoing_processes.keys():
                dep = self.app.get_deployment(dep_id=dep_id)
                self.app._refresh(dep)
                if dep.status in ('complete', 'failed', 'stopped'):
                    to_delete.append(dep_id)
            for done_dep_id in to_delete:
                self.ongoing_processes[dep_id][0].terminate()
                del self.ongoing_processes[done_dep_id]

            time_left = start + self.exit_timeout - datetime.now()
            seconds_left = time_left.total_seconds()
            if not wait or not self.ongoing_processes or seconds_left <= 0:
                break

            log.debug('Waiting %.1fs for children to finish.' % (seconds_left))
            # Old python does not provide timeouts for Popen methods.
            time.sleep(2)

        if to_delete:
            log.debug('Cleaned up deployments that finished.')

        # Halt all deployments taking too long.
        if wait:
            to_delete = self.ongoing_processes.keys()
        else:
            to_delete = self.get_stalled_deployments()

        for stalled_dep_id in to_delete:
            self.ongoing_processes[stalled_dep_id][0].terminate()
            dep = self.app.get_deployment(dep_id=stalled_dep_id)
            self.app._refresh(dep)
            if dep.status not in ('complete', 'failed', 'stopped'):
                dep.status = 'failed'
            self.app.commit_session()
            del self.ongoing_processes[stalled_dep_id]

        if to_delete:
            log.debug('Cleaned up deployments that stalled.')

    def get_stalled_deployments(self):
        """
        Return the list of ongoing deployments that were started more than
        self.threshold ago.
        """
        return [
            dep_id for dep_id in self.ongoing_processes if datetime.now() >
            self.ongoing_processes[dep_id][1] + self.threshold
        ]

    def create_zoo(self, zoo_config):
        """
        Create and return a new zoo.
        """
        hostname = socket.gethostname()

        self.zoo = KazooClient('hosts=%s' % ','.join(zoo_config))
        def state_listener(state):
            if state == KazooState.SUSPENDED:
                log.warning("ZooKeeper connection suspended. Reconnecting...")
                self.election = self.create_zoo(zoo_config)
                self.zk_run = self.election.run
            elif state == KazooState.LOST:
                log.warning("ZooKeeper connection lost.")
            else:
                log.info("Connecting to ZooKeeper...")
        self.zoo.add_listener(state_listener)
        self.zoo.start()
        log.info("Connected to ZooKeeper.")
        return self.zoo.Election('/tdsinstaller', hostname)

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
