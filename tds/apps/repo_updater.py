'''
Updates the deploy yum repsitory with files in the configured directories
'''
import os
import os.path
import time
import shutil
import smtplib
import subprocess
import logging

from email.mime.text import MIMEText

import tagopsdb
import tagopsdb.deploy.package as package
import tagopsdb.exceptions

from ..utils import run

from . import TDSProgramBase

log = logging.getLogger('tds.apps.repo_updater')


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
        self.validate_yum_config()

    def validate_yum_config(self):
        "Make sure we've got all the values we need for the yum repository"

        yum_config = self.config.get('yum', None)

        if yum_config is None:
            raise RuntimeError('YAML configuration missing "yum" section')

        required_keys = ('repo_location', 'incoming', 'processing')
        for key in required_keys:
            if key not in yum_config:
                raise RuntimeError(
                    'YAML configuration missing necessary '
                    'parameter in "yum" section: %s' % key
                )

    def remove_file(self, rpm):
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
            rpm_info = run(cmd)
        except subprocess.CalledProcessError as exc:
            log.error('rpm command failed: %s', exc)

            try:
                self.email_for_invalid_rpm(rpm_to_process)
                # Email send failed?  Tough noogies.
            except smtplib.SMTPException as exc:
                log.error('Email send failed: %s', exc)

        if rpm_info is not None:
            # Contains arch type, package name, version and release
            rpm_info = rpm_info.stdout.split('\n')

        return rpm_info

    def prepare_rpms(self, files):
        """Move RPMs in incoming directory to the processing directory."""

        log.info('Moving files in incoming directory to processing '
                 'directory...')

        self.valid_rpms = dict()

        for rpm in files:
            src_rpm = os.path.join(self.incoming_dir, rpm)
            dst_rpm = os.path.join(self.processing_dir, rpm)

            if not os.path.isfile(src_rpm):
                continue

            rpm_info = self.check_rpm_file(src_rpm)

            if rpm_info is None:
                log.error('Unable to process RPM file')

                self.remove_file(src_rpm)

                # XXX: Unsure what to do here for the database info,
                # since acquiring the proper version and release
                # isn't easily doable from the file name (though
                # it is possible).
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
                          src_rpm, self.processing_dir, e)
                pkg.status = 'failed'
                self.remove_file(src_rpm)
                del self.valid_rpms[rpm]
            else:
                pkg.status = 'processing'
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

        smtp = smtplib.SMTP('localhost')
        smtp.sendmail(sender, receiver_emails, msg.as_string())
        smtp.quit()

    def update_repo(self):
        """Copy RPMs in processing directory to the repository and run
           update the repo.
        """

        for rpm in self.valid_rpms.keys():
            rpm_to_process = os.path.join(self.processing_dir, rpm)
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

            dest_dir = os.path.join(self.repo_dir, rpm_info[0])

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
            run(['make', '-C', self.repo_dir])
        except subprocess.CalledProcessError as exc:
            log.error('yum database update failed, retrying: %s', exc)
            time.sleep(5)   # Short delay before re-attempting

            try:
                run(['make', '-C', self.repo_dir])
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
            self.remove_file(os.path.join(self.processing_dir, rpm_to_process))

    def run(self):
        '''
        Find files in incoming dir and add them to the yum repository
        '''
        files = os.listdir(self.incoming_dir)

        if files:
            log.info('Files found, processing them...')
            self.prepare_rpms(files)
            self.update_repo()
            log.info('Done processing, checking for incoming files...')


    @property
    def incoming_dir(self):
        'Easy access property for yum.incoming config key'
        return self.config['yum.incoming']

    @property
    def processing_dir(self):
        'Easy access property for yum.incoming config key'
        return self.config['yum.processing']

    @property
    def repo_dir(self):
        'Easy access property for yum.repo_location config key'
        return self.config['yum.repo_location']
