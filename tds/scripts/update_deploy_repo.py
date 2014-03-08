import collections
import logging
import os
import os.path
import shlex
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

import tagopsdb.deploy.package as package

from tagopsdb.database import init_session
from tagopsdb.database.meta import Session
from tagopsdb.exceptions import RepoException


logger = logging.getLogger('update_deploy_repo')
daemon = None


class ExtCommandError(Exception):
    pass


class Zookeeper(object):
    """ """

    def __init__(self, hostname, servers):
        """Set up election for Zookeeper"""

        self.zk = KazooClient('hosts=%s' % ','.join(servers))
        self.zk.start()
        # self.zk.add_listener(self.my_listener)
        self.election = self.zk.Election('/deployrepo', hostname)

    def my_listener(self, state):
        """Manage connection to Zookeeper"""

        pass   # Do we need to do anything here?

    def run(self, elect_method, *args):
        """Run passed method with given arguments when election is won"""

        logger.info('Acquiring lock for processing...')
        self.election.run(elect_method, *args)


def run(cmd, expect_return_code=0, env=None, shell=False):
    """Wrapper to run external command"""

    if isinstance(cmd, basestring):
        args = shlex.split(cmd.replace('\\', '\\\\'))
    else:
        args = cmd

    try:
        proc = subprocess.Popen(args, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, env=env, shell=shell)
    except OSError as e:
        exc = subprocess.CalledProcessError(1, args)
        exc.stderr = 'Error using Popen: %s' % e
        exc.stdout = None
        raise exc

    stdout, stderr = proc.communicate()

    if not (expect_return_code is None or
            expect_return_code == proc.returncode):
        exc = subprocess.CalledProcessError(proc.returncode, args)
        exc.stderr = stderr
        exc.stdout = stdout
        raise exc

    Process = collections.namedtuple('Process',
                                     ['stdout', 'stderr', 'returncode'])

    return Process(stdout=stdout, stderr=stderr, returncode=proc.returncode)


class UpdateDeployRepoDaemon(Daemon):
    """"""

    valid_rpms = None

    def remove_file(self, rpm):
        """ """

        try:
            os.unlink(rpm)
        except OSError as e:
            logger.error('Unable to remove file %s: %s', (rpm, e))

    def check_rpm_file(self, rpm_to_process):
        """ """

        rpm_info = None
        cmd = ['rpm', '-qp', '--queryformat',
               '%{arch}\n%{name}\n%{version}\n%{release}',
               rpm_to_process]

        try:
            rpm_info = run(cmd)
        except subprocess.CalledProcessError as e:
            logger.error('rpm command failed: %s', e)

            try:
                self.email_for_invalid_rpm(rpm_to_process)
            except Exception as e:   # Email send failed?  Tough noogies.
                logger.error('Email send failed: %s', e)

        if rpm_info is not None:
            # Contains arch type, package name, version and release
            rpm_info = rpm_info.stdout.split('\n')

        return rpm_info

    def prepare_rpms(self, incoming_dir, process_dir, files):
        """Move RPMs in incoming directory to the processing directory"""

        logger.info('Moving files in incoming directory to processing '
                    'directory...')

        self.valid_rpms = dict()

        for rpm in files:
            src_rpm = os.path.join(incoming_dir, rpm)
            dst_rpm = os.path.join(process_dir, rpm)

            if not os.path.isfile(src_rpm):
                continue

            rpm_info = self.check_rpm_file(src_rpm)

            if rpm_info is None:
                logger.error('Unable to process RPM file')

                self.remove_file(src_rpm)

                # XXX: Unsure what to do here for the database info,
                # XXX: since acquiring the proper version and release
                # XXX: isn't easily doable from the file name (though
                # XXX: it is possible).
                continue

            pkg = package.find_package(*rpm_info[1:])

            if pkg is None:
                name, version, release = rpm_info[1:]
                raise RepoException('Missing entry for package "%s", '
                                    'version %s, revision %s in database'
                                    % (name, version, release))

            self.valid_rpms[rpm] = rpm_info

            try:
                os.rename(src_rpm, dst_rpm)
            except OSError as e:
                logger.error('Unable to move file "%s" to "%s": %s',
                             (src_rpm, process_dir, e))
                pkg.status = 'failed'
                self.remove_file(src_rpm)
                del self.valid_rpms[rpm]
            else:
                pkg.status = 'processing'
            finally:
                Session.commit()

    def email_for_invalid_rpm(self, rpm_file):
        """Send an email to engineering if a bad RPM is found"""

        sender = 'siteops'
        sender_email = '%s@tagged.com' % sender
        receiver_emails = ['eng+tds@tagged.com']

        msg = MIMEText('The RPM file "%s" is invalid, the builder of it '
                       'should check the build process' % rpm_file)

        msg['Subject'] = '[TDS] Invalid RPM file "%s"' % rpm_file
        msg['From'] = sender_email
        msg['To'] = ', '.join(receiver_emails)

        s = smtplib.SMTP('localhost')
        s.sendmail(sender, receiver_emails, msg.as_string())
        s.quit()

    def update_repo(self, repo_dir, process_dir):
        """Copy RPMs in processing directory to the repository and run
           update the repo
        """

        for rpm in self.valid_rpms.keys():
            rpm_to_process = os.path.join(process_dir, rpm)
            rpm_info = self.valid_rpms[rpm]

            logger.info('Verifying file %s and if valid moving to repository',
                        rpm_to_process)

            pkg = package.find_package(*rpm_info[1:])

            if pkg is None:
                name, version, release = rpm_info[1:]
                raise RepoException('Missing entry for package "%s", '
                                    'version %s, revision %s in database'
                                    % (name, version, release))

            # TODO: ensure package is valid (security purposes)

            dest_dir = os.path.join(repo_dir, rpm_info[0])

            try:
                shutil.copy(rpm_to_process, dest_dir)
            except IOError as e:
                time.sleep(2)   # Short delay before re-attempting

                try:
                    shutil.copy(rpm_to_process, dest_dir)
                except IOError as e:
                    pkg.status = 'failed'
                    self.remove_file(rpm_to_process)
                    del self.valid_rpms[rpm]
                    continue
                finally:
                    Session.commit()

            pkg.status = 'completed'
            Session.commit()

        logger.info('Updating repo...')
        old_umask = os.umask(0002)

        try:
            run(['make', '-C', repo_dir])
        except subprocess.CalledProcessError as e:
            logger.error('yum database update failed, retrying: %s', e)
            time.sleep(5)   # Short delay before re-attempting

            try:
                run(['make', '-C', repo_dir])
            except subprocess.CalledProcessError as e:
                # Yes, making the assumption none of the package finds
                # will fail...
                for rpm_to_process, rpm_info in self.valid_rpms.iteritems():
                    pkg = package.find_package(*rpm_info[1:])
                    pkg.status = 'failed'
                    Session.commit()

                logger.error('yum database update failed, aborting: %s', e)

        os.umask(old_umask)
        logger.info('Removing processed files...')
        # Yes, making the assumption none of the package finds will fail...
        # yet again...
        for rpm_to_process, rpm_info in self.valid_rpms.iteritems():
            pkg = package.find_package(*rpm_info[1:])
            pkg.status = 'completed'
            Session.commit()

            self.remove_file(os.path.join(process_dir, rpm_to_process))

    def process_incoming_directory(self, repo_dir, incoming_dir, process_dir):
        """"""

        logger.info('Checking for incoming files...')

        while True:
            files = os.listdir(incoming_dir)

            if files:
                logger.info('Files found, processing them...')
                self.prepare_rpms(incoming_dir, process_dir, files)
                self.update_repo(repo_dir, process_dir)
                logger.info('Done processing, checking for incoming files...')

            time.sleep(1.0)

    def main(self):
        """Read configuration file and get relevant information, then try
           to process files in the incoming directory if single system or
           zookeeper leader in multi-system configuration
        """

        data = None

        logger.info('Reading database access (dbaccess.admin.yml) file')

        with open('/etc/tagops/dbaccess.admin.yml') as db_file:
            try:
                data = yaml.load(db_file.read())
            except yaml.parser.ParserError as e:
                raise RuntimeError('YAML parse error: %s' % e)

        if 'db' not in data:
            raise RuntimeError('YAML configuration missing "db" section')

        try:
            db_user = data['db']['user']
            db_password = data['db']['password']
        except KeyError as e:
            raise RuntimeError('YAML configuration missing necessary '
                               'parameter in "db" section: %s' % e)

        logger.info('Initializing database session')
        init_session(db_user, db_password)

        logger.info('Reading configuration (deploy.yml) file')

        with open('/etc/tagops/deploy.yml') as conf_file:
            try:
                data = yaml.load(conf_file.read())
            except yaml.parser.ParserError, e:
                raise RepoException('YAML parse error: %s' % e)

        if 'yum' not in data:
            raise RuntimeError('YAML configuration missing "yum" section')

        try:
            repo_dir = data['yum']['repo_location']
            incoming_dir = data['yum']['incoming']
            process_dir = data['yum']['processing']
        except KeyError as e:
            raise RuntimeError('YAML configuration missing necessary '
                               'parameter in "yum" section: %s' % e)

        if 'zookeeper' in data:
            hostname = socket.gethostname()

            zk = Zookeeper(hostname, data['zookeeper'])
            zk.run(self.process_incoming_directory, repo_dir, incoming_dir,
                   process_dir)
        else:
            self.process_incoming_directory(repo_dir, incoming_dir,
                                            process_dir)

    def run(self):
        """A wrapper for the main process to ensure any unhandled
           exceptions are logged before the daemon exits
        """

        try:
            self.main()
        except:
            value = sys.exc_info()[1]
            e = "Unhandled exception: %s.  Daemon exiting." % value
            logger.error(e)
            sys.exit(1)


def daemon_main():
    pid = '/var/run/update_deploy_repo.pid'
    logfile = '/var/log/update_deploy_repo.log'

    # 'logger' set at top of program
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    fh = logging.FileHandler(logfile, 'a')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s",
                                  "%b %e %H:%M:%S")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    daemon = UpdateDeployRepoDaemon(pid,
                                    stdout='/tmp/update_deploy_repo.out',
                                    stderr='/tmp/update_deploy_repo.err')

    if len(sys.argv) == 2:
        cmd, arg = sys.argv

        if arg == 'start':
            logger.info('Starting %s daemon' % cmd)
            daemon.start()
        elif arg == 'stop':
            logger.info('Stopping %s daemon' % cmd)
            daemon.stop()
        elif arg == 'restart':
            logger.info('Restarting %s daemon' % cmd)
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