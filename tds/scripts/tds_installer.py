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
from simpledaemon import Daemon

import tagopsdb
import tds.apps
import tds.exceptions
import tds.model
import tds.utils.processes

log = logging.getLogger('tds_installer')


class TDSInstallerDaemon(Daemon):
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
        super(TDSInstallerDaemon, self).__init__(*args, **kwargs)

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
        zookeeper_config = self.app.config.get('zookeeper', None)

        if zookeeper_config is not None:
            self.election = self.create_zoo(zookeeper_config)
            self.zk_run = self.election.run
        else:
            self.zk_run = lambda f, *a, **k: f(*a, **k)

        while not self.should_stop:
            self.zk_run(self.handle_incoming_deployments)
            self.clean_up_processes()
            time.sleep(0.1)     # Increase probability of other daemons running

        self.halt_all_processes()
        log.info("Stopped.")

    def halt_all_processes(self):
        to_delete = list()
        for dep_id in self.ongoing_processes:
            proc = self.ongoing_processes[dep_id][0]
            proc.terminate()
            dep = self.app.get_deployment(dep_id=dep_id)
            self.app._refresh(dep)
            if dep.status not in ('complete', 'failed', 'stopped'):
                dep.status = 'failed'
            self.app.commit_session()
            to_delete.append(dep_id)
        for halted_dep_id in to_delete:
            del self.ongoing_processes[halted_dep_id]

    def handle_incoming_deployments(self):
        """Look for files in 'incoming' directory and handle them."""
        tagopsdb.Session.close()
        deployment = self.app.find_deployment()

        # Heartbeat test to see if daemon is 'stuck'
        if (datetime.now() - self.heartbeat_time).seconds >= 300:
            self.heartbeat_time = datetime.now()
            log.info('HEARTBEAT - Deployment search result: %r', deployment)

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

    def clean_up_processes(self):
        """
        Join processes that have finished and terminate stalled processes.
        """
        to_delete = list()
        # Remove entries for all done subprocesses
        for dep_id in self.ongoing_processes.keys():
            dep = self.app.get_deployment(dep_id=dep_id)
            self.app._refresh(dep)
            if dep.status in ('complete', 'failed', 'stopped'):
                to_delete.append(dep_id)
        for done_dep_id in to_delete:
            del self.ongoing_processes[done_dep_id]

        # Halt all deployments taking too long.
        for stalled_dep_id in self.get_stalled_deployments():
            self.ongoing_processes[stalled_dep_id][0].terminate()
            dep = self.app.get_deployment(dep_id=stalled_dep_id)
            self.app._refresh(dep)
            dep.status = 'failed'
            self.app.commit_session()
            del self.ongoing_processes[stalled_dep_id]

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
    pid = '/var/run/tds_installer.pid'
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

    daemon = TDSInstallerDaemon(
        app,
        pid,
        stdout='/tmp/tds_installer.out',
        stderr='/tmp/tds_installer.err'
    )

    signal.signal(signal.SIGTERM, daemon.sigterm_handler)

    if len(sys.argv) == 2:
        cmd, arg = sys.argv

        if arg == 'start':
            log.info('Starting %s daemon', cmd)
            daemon.start()
        elif arg == 'stop':
            log.info('Stopping %s daemon', cmd)
            daemon.stop()
        elif arg == 'restart':
            log.info('Restarting %s daemon', cmd)
            daemon.restart()
        else:
            print 'Invalid argument'
            sys.exit(2)

        sys.exit(0)
    else:
        print 'Usage: %s {start|stop|restart}' % sys.argv[0]
        sys.exit(0)

if __name__ == '__main__':
    daemon_main()
