"""Program to run a daemon on yum repository servers to manage
   new packages being added to the deploy repository for TDS.
"""

import logging
import os
import os.path
import shutil
import smtplib
import socket
import subprocess
import sys
import time

from email.mime.text import MIMEText

import yaml
import yaml.parser

from kazoo.client import KazooClient   # , KazooState
from simpledaemon import Daemon

import tagopsdb
import tagopsdb.deploy.package as package
import tagopsdb.exceptions

import tds.utils as utils

log = logging.getLogger('update_deploy_repo')


class ExtCommandError(Exception):
    """Custom exception for external command errors."""

    pass


class Zookeeper(object):
    """Zookeeper management object."""

    def __init__(self, hostname, servers):
        """Set up election for Zookeeper."""

        self.zoo = KazooClient('hosts=%s' % ','.join(servers))
        self.zoo.start()
        # self.zoo.add_listener(self.my_listener)
        self.election = self.zoo.Election('/deployrepo', hostname)

    def my_listener(self, state):
        """Manage connection to Zookeeper."""

        pass   # Do we need to do anything here?

    def run(self, elect_method, *args):
        """Run passed method with given arguments when election is won."""

        log.info('Acquiring lock for processing...')
        self.election.run(elect_method, *args)


class UpdateDeployRepoDaemon(Daemon):
    """Daemon to manage updating the deploy repository with new packages."""

    valid_rpms = None

    @staticmethod
    def remove_file(rpm):
        """Remove file from system."""

        try:
            os.unlink(rpm)
        except OSError as exc:
            log.error('Unable to remove file %s: %s', rpm, exc)

    def check_rpm_file(self, rpm_to_process):
        """Ensure file is a valid RPM."""

        rpm_info = None
        cmd = ['rpm', '-qp', '--queryformat',
               '%{arch}\n%{name}\n%{version}\n%{release}',
               rpm_to_process]

        try:
            rpm_info = utils.run(cmd)
        except subprocess.CalledProcessError as exc:
            log.error('rpm command failed: %s', exc)

            try:
                self.email_for_invalid_rpm(rpm_to_process)
            except Exception as exc:   # Email send failed?  Tough noogies.
                log.error('Email send failed: %s', exc)

        if rpm_info is not None:
            # Contains arch type, package name, version and release
            rpm_info = rpm_info.stdout.split('\n')

        return rpm_info

    def prepare_rpms(self, incoming_dir, process_dir, files):
        """Move RPMs in incoming directory to the processing directory."""

        log.info('Moving files in incoming directory to processing '
                 'directory...')

        self.valid_rpms = dict()

        for rpm in files:
            src_rpm = os.path.join(incoming_dir, rpm)
            dst_rpm = os.path.join(process_dir, rpm)

            if not os.path.isfile(src_rpm):
                continue

            rpm_info = self.check_rpm_file(src_rpm)

            if rpm_info is None:
                log.error('Unable to process RPM file')

                self.remove_file(src_rpm)

                # XXX: Unsure what to do here for the database info,
                # XXX: since acquiring the proper version and release
                # XXX: isn't easily doable from the file name (though
                # XXX: it is possible).
                continue

            pkg = package.find_package(*rpm_info[1:])

            if pkg is None:
                name, version, release = rpm_info[1:]
                raise tagopsdb.exceptions.RepoException(
                    'Missing entry for package "%s", '
                    'version %s, revision %s in database'
                    % (name, version, release)
                )

            self.valid_rpms[rpm] = rpm_info

            try:
                os.rename(src_rpm, dst_rpm)
            except OSError as e:
                log.error('Unable to move file "%s" to "%s": %s',
                          src_rpm, process_dir, e)
                pkg.status = 'failed'
                self.remove_file(src_rpm)
                del self.valid_rpms[rpm]
            else:
                pkg.status = 'processing'
            finally:
                tagopsdb.Session.commit()

    @staticmethod
    def email_for_invalid_rpm(rpm_file):
        """Send an email to engineering if a bad RPM is found."""

        sender = 'siteops'
        sender_email = '%s@tagged.com' % sender
        receiver_emails = ['eng+tds@tagged.com']

        msg = MIMEText('The RPM file "%s" is invalid, the builder of it '
                       'should check the build process' % rpm_file)

        msg['Subject'] = '[TDS] Invalid RPM file "%s"' % rpm_file
        msg['From'] = sender_email
        msg['To'] = ', '.join(receiver_emails)

        smtp = smtplib.SMTP('localhost')
        smtp.sendmail(sender, receiver_emails, msg.as_string())
        smtp.quit()

    def update_repo(self, repo_dir, process_dir):
        """Copy RPMs in processing directory to the repository and run
           update the repo.
        """

        for rpm in self.valid_rpms.keys():
            rpm_to_process = os.path.join(process_dir, rpm)
            rpm_info = self.valid_rpms[rpm]

            log.info('Verifying file %s and if valid moving to repository',
                     rpm_to_process)

            pkg = package.find_package(*rpm_info[1:])

            if pkg is None:
                name, version, release = rpm_info[1:]
                raise tagopsdb.exceptions.RepoException(
                    'Missing entry for package "%s", '
                    'version %s, revision %s in database'
                    % (name, version, release)
                )

            # TODO: ensure package is valid (security purposes)

            dest_dir = os.path.join(repo_dir, rpm_info[0])

            try:
                shutil.copy(rpm_to_process, dest_dir)
            except IOError:
                time.sleep(2)   # Short delay before re-attempting

                try:
                    shutil.copy(rpm_to_process, dest_dir)
                except IOError:
                    pkg.status = 'failed'
                    self.remove_file(rpm_to_process)
                    del self.valid_rpms[rpm]
                    continue
                finally:
                    tagopsdb.Session.commit()

        log.info('Updating repo...')
        old_umask = os.umask(0002)
        final_status = 'completed'

        try:
            utils.run(['make', '-C', repo_dir])
        except subprocess.CalledProcessError as exc:
            log.error('yum database update failed, retrying: %s', exc)
            time.sleep(5)   # Short delay before re-attempting

            try:
                utils.run(['make', '-C', repo_dir])
            except subprocess.CalledProcessError as exc:
                log.error('yum database update failed, aborting: %s', exc)
                final_status = 'failed'

        log.info('Updating status of packages to: %s', final_status)
        # Yes, making the assumption none of the package finds
        # will fail...
        for rpm_to_process, rpm_info in self.valid_rpms.iteritems():
            pkg = package.find_package(*rpm_info[1:])
            pkg.status = final_status
            tagopsdb.Session.commit()

        os.umask(old_umask)
        log.info('Removing processed files...')

        for rpm_to_process, rpm_info in self.valid_rpms.iteritems():
            self.remove_file(os.path.join(process_dir, rpm_to_process))

    def process_incoming_directory(self, repo_dir, incoming_dir, process_dir):
        """Look for files in 'incoming' directory and handle them."""

        log.info('Checking for incoming files...')

        while True:
            files = os.listdir(incoming_dir)

            if files:
                log.info('Files found, processing them...')
                self.prepare_rpms(incoming_dir, process_dir, files)
                self.update_repo(repo_dir, process_dir)
                log.info('Done processing, checking for incoming files...')

            time.sleep(1.0)

    def main(self):
        """Read configuration file and get relevant information, then try
           to process files in the incoming directory if single system or
           zookeeper leader in multi-system configuration.
        """

        data = None

        log.info('Reading database access (dbaccess.admin.yml) file')

        with open('/etc/tagops/dbaccess.admin.yml') as db_file:
            try:
                data = yaml.load(db_file.read())
            except yaml.parser.ParserError as e:
                raise RuntimeError('YAML parse error: %s' % e)

        if 'db' not in data:
            raise RuntimeError('YAML configuration missing "db" section')

        try:
            dbconfig = data['db']
            if None in (dbconfig.get('user'), dbconfig.get('password')):
                raise KeyError
        except KeyError as e:
            raise RuntimeError('YAML configuration missing necessary '
                               'parameter in "db" section: %s' % e)

        log.info('Initializing database session')

        tagopsdb.init(dict(
            url=dict(
                username=dbconfig['user'],
                password=dbconfig['password'],
                host=dbconfig['hostname'],
                database=dbconfig['db_name'],
            ),
            pool_recycle=3600)
        )

        log.info('Reading configuration (deploy.yml) file')

        with open('/etc/tagops/deploy.yml') as conf_file:
            try:
                data = yaml.load(conf_file.read())
            except yaml.parser.ParserError as exc:
                raise tagopsdb.exceptions.RepoException(
                    'YAML parse error: %s' % exc
                )

        if 'yum' not in data:
            raise RuntimeError('YAML configuration missing "yum" section')

        try:
            repo_dir = data['yum']['repo_location']
            incoming_dir = data['yum']['incoming']
            process_dir = data['yum']['processing']
        except KeyError as exc:
            raise RuntimeError('YAML configuration missing necessary '
                               'parameter in "yum" section: %s' % exc)

        if 'zookeeper' in data:
            hostname = socket.gethostname()

            zoo = Zookeeper(hostname, data['zookeeper'])
            zoo.run(self.process_incoming_directory, repo_dir, incoming_dir,
                    process_dir)
        else:
            self.process_incoming_directory(repo_dir, incoming_dir,
                                            process_dir)

    def run(self):
        """A wrapper for the main process to ensure any unhandled
           exceptions are logged before the daemon exits.
        """

        try:
            self.main()
        except Exception:
            value = sys.exc_info()[1]
            exc = "Unhandled exception: %s.  Daemon exiting." % value
            log.error(exc)
            sys.exit(1)


def daemon_main():
    """Prepare logging then initialize daemon."""

    pid = '/var/run/update_deploy_repo.pid'
    logfile = '/var/log/update_deploy_repo.log'

    # 'logger' set at top of program
    log.setLevel(logging.DEBUG)
    log.propagate = False
    handler = logging.FileHandler(logfile, 'a')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s",
                                  "%b %e %H:%M:%S")
    handler.setFormatter(formatter)
    log.addHandler(handler)

    daemon = UpdateDeployRepoDaemon(pid,
                                    stdout='/tmp/update_deploy_repo.out',
                                    stderr='/tmp/update_deploy_repo.err')

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
