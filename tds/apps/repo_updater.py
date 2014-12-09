'''
Updates the deploy yum repsitory with files in the configured directories
'''
import sys
import os
import os.path
import time
import shutil
import smtplib
import subprocess
import logging

from email.mime.text import MIMEText

import tagopsdb
import tagopsdb.exceptions

if __package__ is None:
    # This unused import is necessary if the file is executed as a script,
    # usually during testing
    import tds.apps
    __package__ = 'tds.apps'

from .. import utils
from .. import model
from . import TDSProgramBase

log = logging.getLogger('tds.apps.repo_updater')


class RPMQueryProvider(object):
    @classmethod
    def query(cls, filename, fields):
        rpm_format = '\n'.join(
            '%%{field}' for field in fields
        )

        try:
            rpm_query_result = utils.run([
                'rpm', '-qp', '--queryformat',
                rpm_format,
                filename
            ])
        except subprocess.CalledProcessError as exc:
            log.error('rpm command failed: %s', exc)

            return None
        else:
            return zip(
                fields,
                rpm_query_result.stdout.splitlines()
            )


class RPMDescriptor(object):
    query_fields = ('arch', 'name', 'version', 'release')
    arch = None
    name = None
    version = None
    release = None

    def __init__(self, path, **attrs):
        self.path = path

        for key, val in attrs.items():
            setattr(self, key, val)

    @property
    def filename(self):
        return os.path.basename(self.path)

    @property
    def package_info(self):
        info = self.__dict__.copy()
        info.pop('path', None)
        info['revision'] = info.pop('release', None)

        return info

    @property
    def info(self):
        #TODO We shouldn't be doing this dict pop trick.
        # Mike recommended possibly adding a hybrid property to the
        # tagopsdb.model.package.Package class.
        self_info = self.package_info
        self_info.pop('arch')
        return self_info

    @classmethod
    def from_path(cls, path):
        info = RPMQueryProvider.query(path, RPMDescriptor.query_fields)
        if info is None:
            return None
        return cls(path, **dict(info))


class RepoUpdater(TDSProgramBase):
    '''
    TDS app that updates the yum repository based on files
    in the incoming directory
    '''
    valid_rpms = None

    def initialize(self):
        'Init the required config and resources for the app'

        log.info('Initializing database session')
        self.initialize_db()
        self.validate_repo_config()
        try:
            self.email_port = self.config.get('notifications').get('email').get(
                'port', 25
            )
        except KeyError:
            self.email_port = 25

    def validate_repo_config(self):
        "Make sure we've got all the values we need for the yum repository"

        repo_config = self.config.get('repo', None)

        if repo_config is None:
            raise RuntimeError('YAML configuration missing "repo" section')

        required_keys = ('repo_location', 'incoming', 'processing')
        for key in required_keys:
            if key not in repo_config:
                raise RuntimeError(
                    'YAML configuration missing necessary '
                    'parameter in "repo" section: %s' % key
                )

    def remove_file(self, rpm):
        """Remove file from system."""

        try:
            os.unlink(rpm)
        except OSError as exc:
            log.error('Unable to remove file %s: %s', rpm, exc)

    def notify_bad_rpm(self, rpm_path):
        try:
            self.email_for_invalid_rpm(rpm_path)
            # Email send failed?  Tough noogies.
        except smtplib.SMTPException as exc:
            log.error('Email send failed: %s', exc)

    def validate_rpms_in_dir(self, dir):
        good = []
        bad = []

        for name in os.listdir(dir):
            fullpath = os.path.join(dir, name)
            if not os.path.isfile(fullpath):
                continue

            rpm = RPMDescriptor.from_path(fullpath)
            if rpm is None:
                bad.append(name)
            else:
                good.append(rpm)

        return dict(good=good, bad=bad)

    def handle_unprocessable_rpms(self, bad_things):
        for bad_thing in bad_things:
            log.error('Unable to process RPM file')

            self.notify_bad_rpm(bad_thing)
            self.remove_file(bad_thing)

    def prepare_rpms(self):
        """Move RPMs in incoming directory to the processing directory."""

        log.info('Moving files in incoming directory to processing '
                 'directory...')

        incoming_items = self.validate_rpms_in_dir(self.incoming_dir)

        self.handle_unprocessable_rpms(incoming_items.get('bad', []))

        good = incoming_items.get('good', [])
        if not good:
            return

        log.info('Files found, processing them...')

        for rpm in good:
            package = model.Package.get(**rpm.info)

            if package is None:
                log.error(
                    'Missing entry for package "%s", '
                    'version %s, revision %s in database',
                    rpm.name, rpm.version, rpm.release
                )
                self.remove_file(rpm.path)

            try:
                os.rename(
                    rpm.path,
                    os.path.join(self.processing_dir, rpm.filename)
                )
            except OSError as exc:
                log.error('Unable to move file "%s" to "%s": %s',
                          rpm.path, self.processing_dir, exc)
                package.status = 'failed'
                self.remove_file(rpm.path)
            else:
                package.status = 'processing'
            finally:
                tagopsdb.Session.commit()

    def email_for_invalid_rpm(self, rpm_file):
        """Send an email to engineering if a bad RPM is found."""

        sender = 'siteops'
        sender_email = '%s@tagged.com' % sender
        receiver_emails = ['eng+tds@tagged.com']

        msg = MIMEText('The RPM file "%s" is invalid, the builder of it '
                       'should check the build process' % rpm_file)

        msg['Subject'] = '[TDS] Invalid RPM file "%s"' % rpm_file
        msg['From'] = sender_email
        msg['To'] = ', '.join(receiver_emails)

        smtp = smtplib.SMTP('localhost', self.email_port)
        smtp.sendmail(sender, receiver_emails, msg.as_string())
        smtp.quit()

    def process_rpms(self):
        """Copy RPMs in processing directory to the repository and run
           update the repo.
        """
        ready_for_repo = []
        processing_items = self.validate_rpms_in_dir(self.processing_dir)

        self.handle_unprocessable_rpms(processing_items.get('bad', []))

        for rpm in processing_items.get('good', []):
            log.info('Verifying file %s and if valid moving to repository',
                     rpm.path)

            package = model.Package.get(**rpm.info)

            if package is None:
                log.error(
                    'Missing entry for package "%s", '
                    'version %s, revision %s in database',
                    rpm.name, rpm.version, rpm.release
                )
                self.remove_file(rpm.path)

            # TODO: ensure package is valid (security purposes)

            dest_path = os.path.join(self.repo_dir, rpm.filename)

            try:
                shutil.copy(rpm.path, dest_path)
            except IOError:
                time.sleep(2)   # Short delay before re-attempting

                try:
                    shutil.copy(rpm.path, dest_path)
                except IOError:
                    package.status = 'failed'
                    self.remove_file(rpm.path)
                    continue
                finally:
                    tagopsdb.Session.commit()

            ready_for_repo.append((rpm, package))

        if len(ready_for_repo) > 0:
            self.update_repo(ready_for_repo)
            log.info('Done processing.')

    def update_repo(self, rpms_packages):
        log.info('Updating repo...')
        old_umask = os.umask(0002)
        final_status = 'completed'

        try:
            utils.run(['make', '-C', self.repo_dir])
        except subprocess.CalledProcessError as exc:
            log.error('yum database update failed, retrying: %s', exc)
            time.sleep(5)   # Short delay before re-attempting

            try:
                utils.run(['make', '-C', self.repo_dir])
            except subprocess.CalledProcessError as exc:
                log.error('yum database update failed, aborting: %s', exc)
                final_status = 'failed'

        log.info('Updating status of packages to: %s', final_status)
        # Yes, making the assumption none of the package finds
        # will fail...
        for rpm, package in rpms_packages:
            package.status = final_status
            tagopsdb.Session.commit()

        os.umask(old_umask)
        log.info('Removing processed files...')

        for rpm, package in rpms_packages:
            self.remove_file(rpm.path)

    def run(self):
        '''
        Find files in incoming dir and add them to the yum repository
        '''

        self.prepare_rpms()
        self.process_rpms()

    @property
    def incoming_dir(self):
        """Easy access property for repo.incoming config key."""
        return self.config['repo.incoming']

    @property
    def processing_dir(self):
        """Easy access property for repo.incoming config key."""
        return self.config['repo.processing']

    @property
    def repo_dir(self):
        """Easy access property for repo.repo_location config key."""
        return self.config['repo.repo_location']

if __name__ == '__main__':
    def parse_command_line(args):
        # TODO implement parser thing?
        return {
            'config_dir': args[1]
        }
    args = parse_command_line(sys.argv[1:])

    log.setLevel(logging.DEBUG)
    log.propagate = False
    logfile = os.path.join(args['config_dir'], 'update_deploy_repo.log')
    handler = logging.FileHandler(logfile, 'a')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s",
                                  "%b %e %H:%M:%S")
    handler.setFormatter(formatter)
    log.addHandler(handler)

    prog = RepoUpdater(args)
    prog.initialize()
    prog.run()
