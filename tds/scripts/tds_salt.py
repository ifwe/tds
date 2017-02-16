#!/usr/bin/env python2.6
#
# Copyright (C) 2012-2015 Tagged
#
# All rights reserved.

"""Python application to install or restart a given Tagged application"""

import collections
import ConfigParser
import os
import shlex
import signal
import subprocess
import sys
import time

import psutil


# Make sure we're running at least Python 2.6
# and not running Python 3
pyvers = sys.version_info[:2]

if pyvers < (2, 6):
    raise RuntimeError('Python 2.6 is required to use this program')

if pyvers[0] == 3:
    raise RuntimeError('Python 3.x is not supported at this time, please '
                       'use Python 2.6+')


# NOTE: The following three top-level methods are from TDS's
#       utils/processes.py module.  Once a proper TDS 'core' package
#       has been created, it should be imported and these should
#       be removed.
def run(cmd, expect_return_code=0, shell=False, **kwds):
    """Wrapper to run external command"""

    proc = start_process(cmd, shell=shell, **kwds)
    return wait_for_process(proc, expect_return_code=expect_return_code,
                            **kwds)


def start_process(cmd, shell=False, **kwds):
    """
    Start a subprocess.

    Return a token-like object that can be used in a call to
    `wait_for_process` to end the process and get the results.
    """

    if isinstance(cmd, basestring):
        args = shlex.split(cmd.replace('\\', '\\\\'))
    else:
        args = cmd

    args = map(str, args)

    try:
        start = time.time()
        proc = subprocess.Popen(args, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=shell, **kwds)
        proc.cmd = args
        proc.start_time = start
    except OSError as e:
        exc = subprocess.CalledProcessError(1, args)
        exc.stderr = 'Error using Popen: %s' % e
        exc.stdout = None
        raise exc

    return proc


def wait_for_process(proc, expect_return_code=0, **_kwds):
    """
    Finalize a process token and return information about the ended process.

    This is a blocking call if the subprocess has not yet finished.

    process.duration is not strictly correct -- if the process ended
    before the call to this function, the duration will be inflated.
    """

    stdout, stderr = proc.communicate()
    end = time.time()
    duration = end - proc.start_time

    if not (expect_return_code is None or
            expect_return_code == proc.returncode):
        exc = subprocess.CalledProcessError(proc.returncode, proc.cmd)
        exc.stderr = stderr
        exc.stdout = stdout
        exc.duration = duration
        raise exc

    process = collections.namedtuple(
        'Process',
        ['cmd', 'stdout', 'stderr', 'returncode', 'duration']
    )

    return process(
        cmd=proc.cmd,
        stdout=stdout,
        stderr=stderr,
        returncode=proc.returncode,
        duration=duration
    )


class TDSAppManagerError(Exception):
    pass


class TDSAppManager(object):
    """
    """

    def __init__(
            self, app, version=None, do_restart=False, do_uninstall=False
    ):
        """Basic setup and initial checks"""

        self.app = app
        self.version = version
        self.restart = do_restart
        self.uninstall = do_uninstall

        self.tds_conf = '/etc/tagops/tds.conf'

        if sum(
            bool(param) for param in [version, do_restart, do_uninstall]
        ) > 1:
            raise TDSAppManagerError(
                'Only one of these may be defined: '
                'package version, "restart", "uninstall"'
            )

        if self.version:
            try:
                self.version = int(self.version)
            except ValueError:
                raise TDSAppManagerError(
                    'Version passed (%s) was not a number' % self.version
                )

        self.app_check()

    def app_check(self):
        """Verify application is valid and is allowed to be on host"""

        try:
            with open(self.tds_conf) as conf_file:
                config = ConfigParser.SafeConfigParser()
                config.readfp(conf_file)
        except IOError as err:
            raise TDSAppManagerError(
                'Unable to access the configuration file %s: %s'
                % (self.tds_conf, err)
            )

        try:
            apps = config.get('applications', 'valid')
        except ConfigParser.NoOptionError as err:
            raise TDSAppManagerError(
                'Failed to get configuration information: %s' % err
            )

        valid_apps = [x.strip() for x in apps.split(',')]

        if self.app not in valid_apps:
            raise TDSAppManagerError(
                'Application "%s" is not allowed on this system' % self.app
            )

    def get_version(self):
        """Return current version of application on host"""

        vers_cmd = ['/bin/rpm', '-q', '--queryformat', '%{VERSION}', self.app]

        try:
            return run(vers_cmd).stdout
        except subprocess.CalledProcessError:
            # This failing almost certainly means the package isn't
            # installed, so return None
            return None

    @staticmethod
    def manage_services(action):
        """Manage defined application services with a given action"""

        svc_cmd = ['/usr/local/tagops/sbin/services', action]

        try:
            result = run(svc_cmd)
        except subprocess.CalledProcessError as err:
            raise TDSAppManagerError(
                'Failed to run "%s": %s' % (' '.join(svc_cmd), err)
            )

        if result.returncode:
            raise TDSAppManagerError(
                'Action "%s" on defined services failed: %s'
                % (action, result.stderr)
            )

    @staticmethod
    def puppet_check():
        """Check for a running Puppet client process"""

        pids = []

        for proc in psutil.process_iter():
            if (proc.name == 'puppet' and 'agent' in proc.cmdline
                    and proc.username == 'root'):
                pids.append(proc.pid)

        return pids

    @classmethod
    def stop_puppet(cls):
        """Stop the Puppet client process if it's running"""

        running = cls.puppet_check()

        if running:
            print 'Puppet process(es) running, trying to stop nicely'

            for idx in xrange(0, 10):
                for pid in running:
                    try:
                        os.kill(pid, signal.SIGINT)
                    except OSError:
                        # Process already gone, ignore
                        pass

                time.sleep(1)
                running = cls.puppet_check()

                if not running:
                    break
            else:
                print 'Puppet process(es) still running, sending kill'

                for pid in running:
                    os.kill(pid, signal.SIGKILL)

    def verify_install(self):
        """Verify the installed application is the correct version"""

        inst_version = self.get_version()

        if inst_version != self.version:
            raise TDSAppManagerError(
                'Incorrect version of "%s" installed: %s.  Should be %s.'
                % (self.app, inst_version, self.version)
            )

    def perform_install(self):
        """Install the given version of the application on the host"""

        # Acquire current installed version
        inst_version = self.get_version()

        # Compare versions as integers for now; this will need to change
        # if we move to non-integer versions
        if inst_version is None or int(inst_version) < int(self.version):
            yum_op = "install"
        else:
            yum_op = "downgrade"

        makecache_cmd = [
            '/usr/bin/yum', '--disablerepo=*', '--enablerepo=deploy',
            'makecache'
        ]

        try:
            run(makecache_cmd)
        except subprocess.CalledProcessError as err:
            raise TDSAppManagerError(
                'Unable to run "%s": %s' % (' '.join(makecache_cmd), err)
            )

        # Stop any running Puppet agent, then stop services before install
        #
        # NOTE: We don't disable the puppet agent because Puppet will not
        # touch the package on the host if a host deployment entry exists,
        # which will be the case here
        self.stop_puppet()
        self.manage_services('stop')

        install_cmd = [
            '/usr/bin/yum', '-y', '--nogpgcheck', yum_op,
            '%s-%s-1' % (self.app, self.version)
        ]

        try:
            result = run(install_cmd)
        except subprocess.CalledProcessError as err:
            raise TDSAppManagerError(
                'Failed to run "%s": %s' % (' '.join(install_cmd), err)
            )

        if result.returncode:
            raise TDSAppManagerError(
                'Unable to install application "%s" via yum: %s'
                % (self.app, result.stderr)
            )

        # 'yum install/upgrade' may return 0 even with a failure
        # so check to be sure
        inst_version = self.get_version()

        # Currently version is a number, so handle inst_version
        # as such; this will change
        if int(inst_version) != self.version:
            raise TDSAppManagerError(
                'Application "%s" was not installed/upgraded - '
                'Installed: "%r", Expected: "%r"'
                % (self.app, inst_version, self.version)
            )

        # Start services again
        self.manage_services('start')

    def perform_restart(self):
        """Restart the application on the host"""

        self.manage_services('restart')

    def perform_uninstall(self):
        """Uninstall the application on the host"""

        # Stop any running Puppet agent, then stop services before uninstall
        #
        # NOTE: We don't disable the puppet agent because Puppet will not
        # touch the package on the host if a host deployment entry exists,
        # which will be the case here
        self.stop_puppet()
        self.manage_services('stop')

        uninstall_cmd = [
            '/usr/bin/yum', '-y', '--nogpgcheck', 'remove', self.app
        ]

        try:
            result = run(uninstall_cmd)
        except subprocess.CalledProcessError as err:
            raise TDSAppManagerError(
                'Failed to run "%s": %s' % (' '.join(uninstall_cmd), err)
            )

        if result.returncode:
            raise TDSAppManagerError(
                'Unable to uninstall application "%s" via yum: %s'
                % (self.app, result.stderr)
            )

        # 'yum remove' almost always returns 0 even with failures
        inst_version = self.get_version()

        if inst_version is not None:
            raise TDSAppManagerError(
                'Application "%s" was not uninstalled' % self.app
            )

    def perform_task(self):
        """Perform task based on parameters passed"""

        if self.restart:
            self.perform_restart()
        elif self.uninstall:
            self.perform_uninstall()
        else:
            self.perform_install()


# Methods called directly by Salt
def _task(app, **kwargs):
    app_manager = TDSAppManager(app, **kwargs)

    try:
        app_manager.perform_task()
        return 'successful'
    except TDSAppManagerError as err:
        return err


def install(opts):
    app, version = opts
    result = _task(app, version=version)

    if result == 'successful':
        return 'Install of app "%s", version "%s" successful' \
            % (app, version)
    else:
        return 'Install of app "%s", version "%s" failed.  Reason: %s' \
            % (app, version, result)


def restart(opts):
    app = opts[0]  # Single element list
    result = _task(app, do_restart=True)

    if result == 'successful':
        return 'Restart of app "%s" successful' % app
    else:
        return 'Restart of app "%s" failed' % app


def uninstall(opts):
    app = opts[0]  # Single element list
    result = _task(app, do_uninstall=True)

    if result == 'successful':
        return 'Uninstall of app "%s" successful' % app
    else:
        return 'Uninstall of app "%s" failed' % app


# Allow program to be run via command line
def main():
    """ """

    if len(sys.argv) != 3:
        sys.exit(
            'Usage: %s <application> [<version>|restart|uninstall]'
            % sys.argv[0]
        )

    do_restart = False
    do_uninstall = False

    app, version = sys.argv[1:]

    if sys.argv[2] == 'restart':
        do_restart = True
        version = None
    elif sys.argv[2] == 'uninstall':
        do_uninstall = True
        version = None
    else:
        try:
            version = int(sys.argv[2])
        except ValueError:
            sys.exit('Version passed (%s) was not a number' % sys.argv[2])

    app_manager = TDSAppManager(app, version, do_restart, do_uninstall)

    try:
        app_manager.perform_task()
    except TDSAppManagerError as err:
        sys.exit(err)


if __name__ == '__main__':
    main()
