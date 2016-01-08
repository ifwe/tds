"""
Updates the deploy yum repository with files in the configured directories
"""

import errno
import logging
import os
import os.path
import smtplib
import subprocess
import sys
import time
import hashlib

from email.mime.text import MIMEText

import requests
import requests.exceptions
import lxml.html
import jenkinsapi.jenkins
try:
    from jenkinsapi.custom_exceptions import JenkinsAPIException, NotFound
except ImportError:
    from jenkinsapi.exceptions import JenkinsAPIException, NotFound

import tagopsdb
import tagopsdb.exceptions

if __package__ is None:
    # This unused import is necessary if the file is executed as a script,
    # usually during testing
    import tds.apps
    __package__ = 'tds.apps'

from .. import utils
from .. import model
from .. import exceptions
from . import TDSProgramBase

log = logging.getLogger('tds.apps.repo_updater')


class RepoUpdater(TDSProgramBase):
    """
    TDS app that updates the yum repository based on files
    in the incoming directory
    """

    valid_rpms = None

    def initialize(self):
        """Init the required config and resources for the app"""
        log.info('Initializing database session')
        self.initialize_db()
        self.validate_repo_config()
        try:
            self.email_port = self.config.get('notifications')\
                                         .get('email')\
                                         .get('port', 25)
        except KeyError:
            self.email_port = 25
        try:
            self.email_receiver = self.config.get('notifications')\
                                             .get('email')\
                                             .get('receiver')
        except KeyError:
            self.email_receiver = None
        try:
            self.jenkins_url = self.config.get('jenkins').get('url')
        except KeyError:
            raise exceptions.ConfigurationError(
                'Unable to get Jenkins URL from config file.'
            )
        self.jenkins_direct_url = self.config.get('jenkins').get(
            'direct_url', None
        )
        self.max_attempts = self.config.get('jenkins').get(
            'max_download_attempts', 3
        )

    def validate_repo_config(self):
        """
        Make sure we've got all the values we need for the yum repository
        """
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

    @staticmethod
    def remove_file(rpm):
        """Remove file from system."""
        try:
            os.unlink(rpm)
        except OSError as exc:
            if exc.errno == errno.ENOENT:
                pass
            else:
                log.error('Unable to remove file %s: %s', rpm, exc)

    def notify_bad_rpm(self, rpm_path):
        """
        Notify for a bad RPM.
        """
        try:
            self.email_for_invalid_rpm(rpm_path)
            # Email send failed?  Tough noogies.
        except smtplib.SMTPException as exc:
            log.error('Email send failed: %s', exc)

    def _download_rpms(self):
        """
        Determine the RPMs that need to be downloaded by reading the database
        and download those RPMs into the self.incoming_dir directory.
        """
        rpms = list()
        self.pending_pkgs = tagopsdb.Package.find(status='pending')
        if not self.pending_pkgs:
            return
        try:
            jenkins = jenkinsapi.jenkins.Jenkins(self.jenkins_url)
        except Exception:
            raise exceptions.FailedConnectionError(
                'Unable to contact Jenkins server at {url}.'.format(
                    url=self.jenkins_url,
                )
            )

        for pkg in self.pending_pkgs:
            rpm_name = '{name}-{version}-{revision}.{arch}.rpm'.format(
                name=pkg.application.pkg_name,
                version=pkg.version,
                revision=pkg.revision,
                arch=pkg.application.arch,
            )
            rpm_path = os.path.join(self.incoming_dir, rpm_name)
            try:
                rpm = self._download_rpm_for_pkg(
                    pkg, jenkins, rpm_name, rpm_path
                )
            except exceptions.TDSException as exc:
                if os.path.isfile(rpm_path):
                    self.remove_file(rpm_path)
                log.error('Failed to download RPM for package with id={id}: '
                          '{exc}'.format(id=pkg.id, exc=exc))
                pkg.status = 'failed'
                tagopsdb.Session.commit()
            else:
                rpms.append(rpm)

        return rpms

    def _download_rpm_for_pkg(self, pkg, jenkins, rpm_name, rpm_path):
        """
        Download the RPM for the given package. Raise an error on failure.
        """
        pkg.status = 'processing'
        tagopsdb.Session.commit()

        job_name = pkg.job
        matrix_name = None
        if '/' in job_name:
            job_name, matrix_name = job_name.split('/', 1)
        job = jenkins[job_name]
        build = job.get_build(int(pkg.version))
        if matrix_name is not None:
            build = [run for run in build.get_matrix_runs() if matrix_name
                     in run.baseurl][0]

        fingerprint_md5 = self._get_jenkins_fingerprint_md5(
            job_name, rpm_name, pkg.version,
        )
        for _attempt in range(self.max_attempts):
            try:
                artifact = build.get_artifact_dict()[rpm_name]
                rpm_url = artifact.url
            except (KeyError, JenkinsAPIException, NotFound):
                raise exceptions.JenkinsJobNotFoundError(
                    'Artifact', job_name, pkg.version, self.jenkins_url,
                )

            if self.jenkins_direct_url is not None:
                rpm_url = rpm_url.replace(
                    self.jenkins_url, self.jenkins_direct_url,
                )

            req = requests.get(rpm_url)

            if req.status_code != requests.codes.ok:
                raise exceptions.JenkinsJobNotFoundError(
                    'Artifact', job_name, pkg.version, self.jenkins_url,
                )
            data = req.content
            with open(rpm_path, 'wb') as rpm_file:
                rpm_file.write(data)
                rpm_file.flush()
                os.fsync(rpm_file.fileno())

            md5 = hashlib.md5()
            with open(rpm_path) as rpm_file:
                md5.update(rpm_file.read())
                file_md5 = md5.hexdigest()

            if fingerprint_md5 is None or fingerprint_md5.lower() == \
                    file_md5.lower():
                break
            else:
                self.remove_file(rpm_path)
        else:
            raise exceptions.JenkinsJobTransferError(
                'Artifact', job_name, pkg.verion, self.jenkins_url,
            )

        rpm = utils.rpm.RPMDescriptor.from_path(rpm_path)
        if rpm is None:
            self.notify_bad_rpm(rpm_name)
            raise exceptions.InvalidRPMError(
                'Package {rpm_name} is an invalid RPM.'.format(
                    rpm_name=rpm_name
                )
            )
        else:
            return rpm

    def _get_jenkins_fingerprint_md5(self, job_name, rpm_name, version):
        """
        Acquire the Jenkins fingerprint MD5 for the given package.
        This may return 'None' if fingerprinting has not been enabled
        for the given job (specifically for the RPM artifacts).
        """

        # Grab the 'fingerprints' page for the job
        req = requests.get(os.path.join(
            self.jenkins_url, 'job', job_name,
            version, 'fingerprints', ''
        ))

        # The XPath is to extract an href from a row in a table
        # where the artifact matches the RPM file
        html = lxml.html.fromstring(req.content)
        xpath = (
            '//td[re:test(.,"(?<!\w)%s")]/../td[contains(.,"details")]/a/@href'
            % rpm_name.replace('.', '\.')
        )
        fingerprint_href = html.xpath(
            xpath,
            namespaces = {'re': 'http://exslt.org/regular-expressions'}
        )

        # Found an href?  Get the md5 in it (last part of the path)!
        # Otherwise let user know it's not there
        if fingerprint_href:
            return fingerprint_href[0].split('/')[-2]
        else:
            return None

    def prepare_rpms(self):
        """Move RPMs in incoming directory to the processing directory."""
        rpms = self._download_rpms()

        if not rpms:
            return

        log.info('Valid files found, moving them from incoming directory '
                 'to processing directory to be processed...')

        good = list()
        for rpm in rpms:
            package = model.Package.get(**rpm.info)

            if package is None:
                log.error(
                    'Missing entry for package "%s", '
                    'version %s, revision %s in database',
                    rpm.name, rpm.version, rpm.release
                )
                self.remove_file(rpm.path)
                continue

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
                rpm.path = os.path.join(self.processing_dir, rpm.filename)
                good.append(rpm)
            finally:
                tagopsdb.Session.commit()

        return good

    def email_for_invalid_rpm(self, rpm_file):
        """Send an email to engineering if a bad RPM is found."""
        sender = 'siteops'
        sender_email = '%s@tagged.com' % sender
        receiver_emails = ['eng+tds@tagged.com']
        if self.email_receiver is not None:
            receiver_emails.append(self.email_receiver)

        msg = MIMEText('The RPM file "%s" is invalid, the builder of it '
                       'should check the build process' % rpm_file)

        msg['Subject'] = '[TDS] Invalid RPM file "%s"' % rpm_file
        msg['From'] = sender_email
        msg['To'] = ', '.join(receiver_emails)

        smtp = smtplib.SMTP('localhost', self.email_port)
        smtp.sendmail(sender, receiver_emails, msg.as_string())
        smtp.quit()

    def process_rpms(self, rpms):
        """Copy RPMs in processing directory to the repository and run
           update the repo.
        """
        ready_for_repo = []

        if not rpms:
            return

        for rpm in rpms:
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
                continue

            # TODO: ensure package is valid (security purposes)

            dest_file = os.path.join(self.repo_dir, rpm.arch, rpm.filename)

            try:
                self.remove_file(dest_file)
                os.link(rpm.path, dest_file)
            except IOError:
                time.sleep(2)   # Short delay before re-attempting

                try:
                    self.remove_file(dest_file)
                    os.link(rpm.path, dest_file)
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
        """
        Update the repo with the given RPMs.
        """
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
        """
        Find files in incoming dir and add them to the yum repository
        """
        rpms = self.prepare_rpms()
        self.process_rpms(rpms)

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
    def parse_command_line(cl_args):
        """
        Parse command line and return dict of them.
        """
        # TODO implement parser thing?
        return {
            'config_dir': cl_args[1]
        }
    args = parse_command_line(sys.argv[1:])

    log.setLevel(logging.DEBUG)
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
