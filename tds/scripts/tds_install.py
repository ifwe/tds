#!/usr/bin/env python2.6
#
# Copyright (C) 2012-2013 Tagged
#
# All rights reserved.

"""Python application to install a given Tagged application"""

import ConfigParser
import os
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


class ExtCommandError(Exception):
    pass


def run_command(cmd):
    """Wrapper to run external command"""

    print "running: ", " ".join(cmd)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

    stdout, stderr = proc.communicate()

    if proc.returncode:
        cmdline = ' '.join(cmd)
        raise ExtCommandError('Command "%s" failed:\n%s'
                              % (cmdline, stderr))

    return stdout


def puppet_check():
    """Check for a running Puppet client process"""

    pids = []

    for proc in psutil.process_iter():
        if proc.name == 'puppetd':
            pids.append(proc.pid)

    if pids:
        return pids
    else:
        return None


def app_check(app):
    """Ensure requested application is allowed on the system"""

    tds_conf = '/etc/tagops/tds.conf'

    try:
        with open(tds_conf) as conf_file:
            config = ConfigParser.SafeConfigParser()
            config.readfp(conf_file)
    except IOError, e:
        sys.exit('Unable to access the configuration file %s: %s'
                 % (tds_conf, e))

    try:
        apps = config.get('applications', 'valid')
    except ConfigParser.NoOptionError, e:
        sys.exit('Failed to get configuration information: %s' % e)

    valid_apps = [ x.strip() for x in apps.split(',') ]

    if app not in valid_apps:
        sys.exit('Application "%s" is not allowed on this system' % app)


def stop_puppet():
    """Stop the Puppet client process if it's running"""

    running = puppet_check()

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
            running = puppet_check()

            if not running:
                break
        else:
            print 'Puppet process(es) still running, sending kill'

            for pid in running:
                os.kill(pid, signal.SIGKILL)


def manage_services(action):
    """Manage a defined application services with a given action"""

    svc_cmd = [ '/usr/local/tagops/sbin/services', action ]

    try:
        run_command(svc_cmd)
    except ExtCommandError, e:
        sys.exit('Failed to perform action "%s" on defined services: %s'
                 % (action, e))


def app_install(app, version, inst_version):
    """Install the given version of the application"""

    # Compare versions as integers for now; this will need to change
    # if we move to non-integer versions
    if inst_version is None or int(inst_version) < int(version):
        yum_op = "install"
    else:
        yum_op = "downgrade"

    makecache_cmd = [ '/usr/bin/yum', 'makecache' ]
    try:
        run_command(makecache_cmd)
    except ExtCommandError, e:
        sys.exit('Unable to run "yum makecache": %s' % e)

    # Stop services before install, then restart them after install
    manage_services('stop')

    install_cmd = [ '/usr/bin/yum', '-y', '--nogpgcheck', yum_op,
                    '%s-%s-1' % (app, version) ]
    try:
        output = run_command(install_cmd)
    except ExtCommandError, e:
        sys.exit('Unable to install application via yum: %s' % e)

    manage_services('start')


def app_uninstall(app):
    """Uninstall the application"""

    # Stop service before uninstall, no need to restart
    manage_services('stop')

    uninstall_cmd = [ '/usr/bin/yum', '-y', '--nogpgcheck', 'remove', app ]

    try:
        output = run_command(uninstall_cmd)
    except ExtCommandError, e:
        sys.exit('Unable to uninstall application via yum: %s' % e)


def get_version(app):
    """Return current version of application"""

    vers_cmd = [ '/bin/rpm', '-q', '--queryformat', '%{VERSION}', app ]

    return run_command(vers_cmd)


def verify_install(app, version):
    """Verify the installed application is the correct version"""

    try:
        inst_version = get_version(app)
    except ExtCommandError, e:
        sys.exit('Unable to query for installed version of "%s": %s'
                 % (app, e))

    if inst_version != version:
        sys.exit('Incorrect version of "%s" installed: %s.  Should be '
                 '%s.' % (app, inst_version, version))


def main():
    """ """

    if len(sys.argv) != 3:
        sys.exit('Usage: %s <application> [<version>|restart]' % sys.argv[0])

    restart = False
    uninstall = False

    if sys.argv[2] == 'restart':
        restart = True
    elif sys.argv[2] == 'uninstall':
        uninstall = True
    else:
        try:
            int(sys.argv[2])
        except ValueError:
            sys.exit('Version passed (%s) was not a number' % sys.argv[2])

    app, version = sys.argv[1:]
    app_check(app)

    if restart:
        manage_services('restart')
    elif uninstall:
        stop_puppet()
        app_uninstall(app)
    else:
        try:
            inst_version = get_version(app)
        except ExtCommandError:
            inst_version = None   # Assume app not installed
        if inst_version == version:
            return   # Nothing to do

        stop_puppet()
        app_install(app, version, inst_version)
        verify_install(app, version)


if __name__ == '__main__':
    main()
