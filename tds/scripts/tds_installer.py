"""Program to run a daemon on yum repository servers to manage
   new packages being added to the deploy repository for TDS.
"""

import logging
import socket
import sys
import time
import signal
import traceback

from kazoo.client import KazooClient   # , KazooState
from simpledaemon import Daemon

import tds.apps

log = logging.getLogger('tds_installer')


class TDSInstallerDaemon(Daemon):
    """Daemon to manage updating the deploy repository with new packages."""

    should_stop = False
    election = None

    def __init__(self, app, *args, **kwargs):
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
        """Read configuration file and get relevant information, then try
           to process files in the incoming directory if single system or
           zookeeper leader in multi-system configuration.
        """

        self.app.initialize()
        zookeeper_config = self.app.config.get('zookeeper', None)

        if zookeeper_config is not None:
            self.election = self.create_zoo(zookeeper_config)
            run = self.election.run
        else:
            run = lambda f, *a, **k: f(*a, **k)

        run(self.handle_incoming_deployments)

    def handle_incoming_deployments(self):
        """Look for files in 'incoming' directory and handle them."""

        log.info('Checking for waiting deployments...')

        while not self.should_stop:
            self.app.run()
            time.sleep(1.0)

        log.info("Stopped.")

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
