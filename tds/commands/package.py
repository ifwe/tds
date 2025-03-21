# Copyright 2016 Ifwe Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Commands to support managing packages in the TDS system."""

import hashlib
import logging
import os.path
import signal
import time

import jenkinsapi.jenkins
try:
    from jenkinsapi.custom_exceptions import JenkinsAPIException, NotFound
except ImportError:
    from jenkinsapi.exceptions import JenkinsAPIException, NotFound

import lxml.html
import requests
import requests.exceptions

import tagopsdb
import tagopsdb.exceptions
import tagopsdb.deploy.repo
import tagopsdb.deploy.deploy
import tagopsdb.deploy.package

import tds.exceptions
from .base import BaseController, validate
from .. import utils

log = logging.getLogger('tds')


def processing_handler(*_args):
    """This handler is called if the file in the incoming or processing
       directory is not removed in a given amount of time, meaning the
       repository server had a failure.
    """

    raise tagopsdb.exceptions.PackageException(
        'The file placed in the incoming or '
        'processing queue was not removed.\n'
        'Please open a JIRA issue in the TDS project.'
    )


class PackageController(BaseController):
    """Commands to manage packages for supported applications."""

    access_levels = {
        'list': 'environment',
        'add': 'environment',
        'delete': 'environment',
    }

    @property
    def jenkins_url(self):
        """
        Return the Jenkins URL in self.app_config.
        """
        return self.app_config['jenkins.url']

    def _refresh(self, obj):
        """
        WTF
        """
        tagopsdb.Session.commit()
        obj.refresh()

    def _display_status(self, package):
        """
        Display the current status of the package.
        """
        log.info('Status:\t\t[{status}]'.format(status=package.status))

    def _display_output(self, package):
        """
        Display status changes as the package is being updated by the daemon.
        """
        while package.status not in ('processing', 'failed', 'completed'):
            time.sleep(0.1)
            self._refresh(package)
        curr_status = package.status
        self._display_status(package)
        if curr_status == 'processing':
            while package.status not in ('failed', 'completed'):
                time.sleep(0.1)
                self._refresh(package)
            self._display_status(package)

    def _manage_attached_session(self, package):
        """
        Display updates on status of package as daemon works on it.
        """
        log.info('Package now being added, press Ctrl-C at any time to detach '
                 'session...')

        try:
            self._display_output(package)
        except KeyboardInterrupt:
            log.info('Session detached.')
            return dict()

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

    @validate('application')
    def add(
        self, application, version, user, job=None, force=False, **params
    ):
        """
        Add a given version of a package for a given application
        """
        revision = '1'

        try:
            int(version)
        except ValueError:
            log.log("Version must be an integer. Got {version}.".format(
                version=version
            ))
            return dict()

        if job is None:
            job = application.path

        commit_hash = self._validate_jenkins_build(
            application, version, revision, job
        )

        rpm_name = '{name}-{version}-{revision}.{arch}.rpm'.format(
            name=application.pkg_name,
            version=version,
            revision=revision,
            arch=application.arch,
        )
        fingerprint_md5 = self._get_jenkins_fingerprint_md5(
            job, rpm_name, version,
        )
        if fingerprint_md5 is None:
            log.info(
                "WARNING: Fingerprinting is not enabled, your RPM "
                "will not be validated first.  Please see:\n"
                "https://javadoc.jenkins.io/hudson/tasks/ArtifactArchiver.html#setFingerprint(boolean)\n"
                "for information on how to enable it. Continuing..."
            )

        package = application.get_version(version=version, revision=revision)

        if package is not None:
            if package.status == 'failed':
                log.info("Package already exists with failed status. Changing "
                         "status to pending for daemon to attempt "
                         "re-adding...")
            elif not force:
                log.info("Package already exists with status {status}.".format(
                    status=package.status,
                ))
                return dict()
            elif package.status in ('pending', 'processing'):
                log.info("Package already {stat} by daemon. Added {added} by "
                         "{user}.".format(
                            stat="pending addition" if package.status ==
                                "pending" else "being processed",
                            added=package.created,
                            user=package.creator,
                         ))
                return dict()
            elif package.status in ('removed', 'completed'):
                log.info("Package was previously {status}. Changing status to "
                         "pending again for daemon to attempt re-adding..."
                         .format(status=package.status))

        else:
            try:
                package = application.create_version(
                    version=version,
                    revision=revision,
                    job=job,
                    creator=user,
                )
            except tagopsdb.exceptions.PackageException as e:
                log.error(e)
                raise tds.exceptions.TDSException(
                    'Failed to add package {name}@{version}.'.format(
                        name=application.name,
                        version=version,
                    )
                )

        if commit_hash is not None:
            package.commit_hash = commit_hash

        package.status = 'pending'
        tagopsdb.Session.commit()
        if params['detach']:
            log.info('Package ready for repo updater daemon. Disconnecting '
                     'now.')
            return dict()
        return self._manage_attached_session(package)

    def _validate_jenkins_build(self, application, version, revision,
                                job_name):
        """
        Validate that a Jenkins build exists for a package being added.
        Return the revision (e.g., git commit hash) if the build exists and is
        valid.
        """
        try:
            jenkins = jenkinsapi.jenkins.Jenkins(self.jenkins_url)
        except Exception:
            raise tds.exceptions.FailedConnectionError(
                'Unable to contact Jenkins server at {url}.'.format(
                    url=self.jenkins_url,
                )
            )

        matrix_name = None
        if '/' in job_name:
            job_name, matrix_name = job_name.split('/', 1)

        try:
            job = jenkins[job_name]
        except KeyError:
            raise tds.exceptions.JenkinsJobNotFoundError(
                "Job", job_name, version, self.jenkins_url,
            )

        try:
            build = job.get_build(int(version))
        except (KeyError, JenkinsAPIException, NotFound):
            raise tds.exceptions.JenkinsJobNotFoundError(
                "Build", job_name, version, self.jenkins_url,
            )

        if matrix_name is not None:
            for run in build.get_matrix_runs():
                if matrix_name in run.baseurl:
                    build = run
                    break
            else:
                raise tds.exceptions.JenkinsJobNotFoundError(
                    "Matrix build", job_name, version, self.jenkins_url,
                )
        try:
            return build.get_revision()
        except:             # Not sure what exception will be raised --KN
            return None

    @validate('package')
    def delete(self, package, **params):
        """
        Delete a given version of a package for a given project.
        """

        log.debug(
            'Deleting version %s of the package for application "%s" '
            'from software repository', params['version'],
            package.application.name
        )

        try:
            # The real 'revision' is hardcoded to 1 for now
            # This needs to be changed at some point
            tagopsdb.deploy.package.delete_package(
                package.application.name,
                params['version'],
                '1'
            )
        except tagopsdb.exceptions.PackageException as e:
            log.error(e)
            return

        tagopsdb.Session.commit()
        log.debug('Committed database changes')

    @validate('application')
    def list(self, applications=None, **_params):
        """
        Show information for all existing packages in the software repository
        for requested projects (or all projects).
        """

        if not applications:
            applications = tds.model.Application.all()

        packages_sorted = sorted(
            tagopsdb.deploy.package.list_packages(
                [x.name for x in applications] or None
            ),
            key=lambda pkg: (pkg.name, pkg.created, pkg.version, pkg.revision)
        )

        return dict(result=packages_sorted)
