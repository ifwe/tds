"""
Daemon to do installations on servers.
Interacts with Zookeeper to get lock for grabbing queued deployments from DB.
When it grabs the lock, it calls self.app.run().
self.app is passed in during initialization and should be of type Installer,
from tds.apps.installer.
"""

from datetime import datetime, timedelta
import logging
import socket
import sys
import time
import signal
import traceback

from multiprocessing import Process

from kazoo.client import KazooClient   # , KazooState
from simpledaemon import Daemon

import tds.apps

log = logging.getLogger('tds_installer')


class TDSInstallerDaemon(Daemon):
    """Daemon to manage updating the deploy repository with new packages."""

    should_stop = False
    election = None

    def __init__(self, app, *args, **kwargs):
        # ongoing_deployments is a dict with ID keys and values of form:
        # (deployment_id, time_of_deployment_start)
        self.ongoing_deployments = dict()
        # ongoing_processes is a dict with deployment ID keys and values
        # pointing to the process running that deployment
        self.ongoing_processes = dict()
        self.threshold = kwargs.pop('threshold') if 'threshold' in kwargs \
            else timedelta(minutes=30)
        self.app = app
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
        self.app.initialize()
        zookeeper_config = self.app.config.get('zookeeper', None)

        if zookeeper_config is not None:
            self.election = self.create_zoo(zookeeper_config)
            run = self.election.run
        else:
            run = lambda f, *a, **k: f(*a, **k)

        while not self.should_stop:
            run(self.handle_incoming_deployments)
            self.clean_up_processes()
            time.sleep(0.1)     # Increase probability of other daemons running

        self.halt_all_processes()
        log.info("Stopped.")

    def halt_all_processes(self):
        to_delete = list()
        for dep_id in self.ongoing_processes:
            proc = self.ongoing_processes[dep_id]
            proc.terminate()
            proc.join()
            dep = self.app.get_deployment(dep_id=dep_id)
            self.app._refresh(dep)
            if dep.status not in ('complete', 'failed', 'stopped'):
                dep.status = 'failed'
            self.app.commit_session()
            to_delete.append(dep_id)
        for halted_dep_id in to_delete:
            del self.ongoing_processes[halted_dep_id]
            del self.ongoing_deployments[halted_dep_id]

    def handle_incoming_deployments(self):
        """Look for files in 'incoming' directory and handle them."""
        log.info('Checking for queued deployments...')

        deployment = self.app.find_deployment()
        if deployment is None:
            return

        deployment.status = 'inprogress'
        tagopsdb.Session.commit()
        deployment_process = Process(
            target=self.app.do_serial_deployment,
            args=(deployment,),
        )
        self.ongoing_deployments[deployment.id] = (
            deployment.id, datetime.now()
        )
        self.ongoing_processes[deployment.id] = deployment_process
        deployment_process.start()

    def clean_up_processes(self):
        """
        Join processes that have finished and terminate stalled processes.
        """
        to_delete = list()
        # Join all done deployment processes
        for dep_id in self.ongoing_deployments.keys():
            dep = self.app.get_deployment(dep_id=dep_id)
            self.app._refresh(dep)
            if dep.status in ('complete', 'failed', 'stopped'):
                self.ongoing_processes[dep_id].join()
                to_delete.append(dep_id)
        for done_dep_id in to_delete:
            del self.ongoing_processes[done_dep_id]
            del self.ongoing_deployments[done_dep_id]

        # Halt all deployments taking too long.
        for stalled_dep_id in self.get_stalled_deployments():
            proc = self.ongoing_processes[stalled_dep_id]
            proc.terminate()
            proc.join()
            dep = self.app.get_deployment(dep_id=stalled_dep_id)
            self.app._refresh(dep)
            dep.status = 'failed'
            self.app.commit_session()
            del self.ongoing_processes[stalled_dep_id]
            del self.ongoing_deployments[stalled_dep_id]

    def get_stalled_deployments(self):
        """
        Return the list of ongoing deployments that were started more than
        self.threshold ago.
        """
        return [
            dep_id for dep_id in self.ongoing_deployments if datetime.now() >
            self.ongoing_deployments[dep_id][1] + self.threshold
        ]

    @staticmethod
    def create_zoo(zoo_config):
        """
        Create and return a new zoo.
        """
        hostname = socket.gethostname()

        zoo = KazooClient('hosts=%s' % ','.join(zoo_config))
        zoo.start()
        return zoo.Election('/tdsinstaller', hostname)

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
