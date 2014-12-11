"""Commands to support managing packages in the TDS system."""

import logging
import os.path
import signal
import time

import jenkinsapi.jenkins
try:
    from jenkinsapi.custom_exceptions import JenkinsAPIException, NotFound
except ImportError:
    from jenkinsapi.exceptions import JenkinsAPIException, NotFound

import tagopsdb
import tagopsdb.exceptions
import tagopsdb.deploy.repo
import tagopsdb.deploy.deploy
import tagopsdb.deploy.package

import tds.exceptions
from .base import BaseController, validate

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

    def wait_for_state_change(self, package):
        """Check for state change for package in database"""

        while True:
            previous_status = package.status
            tagopsdb.Session.commit()  # WTF
            package.refresh()

            if package.status == 'completed':
                break

            if package.status == 'failed':
                # TODO: why did it fail? user needs to know
                log.info(
                    'Failed to update repository with package '
                    'for application "%s", version %s',
                    package.name, package.version
                )
                log.info('Please try again')
                break

            if package.status != previous_status:
                log.log(5, 'State of package is now: %s', package.status)

            time.sleep(0.5)

    @property
    def jenkins_url(self):
        return self.app_config['jenkins.url']

    def _queue_rpm(self, queued_rpm, rpm_name, package, job_name):
        """Move requested RPM into queue for processing"""

        try:
            jenkins = jenkinsapi.jenkins.Jenkins(self.jenkins_url)
        except Exception:
            raise tds.exceptions.FailedConnectionError(
                'Unable to contact Jenkins server "%s"', self.jenkins_url
            )

        matrix_name = None
        #assume matrix build
        if '/' in job_name:
            job_name, matrix_name = job_name.split('/', 1)

        try:
            job = jenkins[job_name]
        except KeyError:
            raise tds.exceptions.NotFoundError('Job', [job_name])

        try:
            int(package.version)
        except ValueError:
            raise Exception(
                ('Package "%s@%s" does not have an integer version'
                 ' for fetching from Jenkins'),
                package.name, package.version
            )

        try:
            build = job.get_build(int(package.version))
        except (
            KeyError,
            JenkinsAPIException,
            NotFound
        ) as exc:
            log.error(exc)
            raise tds.exceptions.JenkinsJobNotFoundError(
                'Build',
                job_name,
                package.version,
                self.jenkins_url,
            )

        if matrix_name is not None:
            for run in build.get_matrix_runs():
                if matrix_name in run.baseurl:
                    build = run
                    break
            else:
                log.error('could not find matrix run %s', matrix_name)
                raise Exception(
                    'No matrix run matching "%s" for job "%s"',
                    matrix_name, job_name
                )

        try:
            artifacts = build.get_artifact_dict()[rpm_name]
            data = artifacts.get_data()
        except (
            KeyError,
            JenkinsAPIException,
            NotFound
        ):
            raise tds.exceptions.JenkinsJobNotFoundError(
                'Artifact',
                job_name,
                package.version,
                self.jenkins_url,
            )

        tmpname = os.path.join(
            os.path.dirname(os.path.dirname(queued_rpm)), 'tmp', rpm_name
        )

        for tmpfile in (tmpname, queued_rpm):
            tmpdir = os.path.dirname(tmpfile)
            if not os.path.isdir(tmpdir):
                os.makedirs(tmpdir)

        with open(tmpname, 'wb') as tmp_rpm:
            tmp_rpm.write(data)

        os.link(tmpname, queued_rpm)
        os.unlink(tmpname)

    @validate('application')
    def add(self, application, version, **params):
        """Add a given version of a package for a given project"""

        if params.get('force', None):
            raise Exception('Force not implemented yet')

        log.debug(
            'Adding version %s of the package for project "%s" '
            'to software repository', version,
            application.name
        )

        # The real 'revision' is hardcoded to 1 for now
        # This needs to be changed at some point
        revision = '1'

        package = application.get_version(version=version, revision=revision)

        if package is None:
            try:
                package = application.create_version(
                    version=version,
                    revision=revision,
                    creator=params['user']
                )
            except tagopsdb.exceptions.PackageException as e:
                log.error(e)
                raise Exception(
                    'Failed to add package "%s@%s"', package.name,
                    package.version
                )
        else:
            if package.status == 'processing':
                # TODO: verify still processing -- check processing directory
                # if in processing directory, stop and raise exception (in progress)
                # else, fix it by moving the file from processing to incoming,
                # and state to pending. then continue this function
                raise NotImplementedError
            elif package.status != 'failed':
                # possible states: completed, processing, or removed
                # TODO: separate messages for each state.
                raise tds.exceptions.AlreadyExistsError(
                    'Package "%s@%s-%s" already exists',
                    package.name, package.version, revision
                )
            else:
                # package is failed. set it back to pending and try again
                package.status = 'pending'
                tagopsdb.Session.commit()

        # TODO: add property to Package to generate this
        rpm_name = '%s-%s-%s.%s.rpm' % (
            application.pkg_name, version, revision, application.arch
        )

        incoming_dir = params['repo']['incoming']

        pending_rpm = os.path.join(incoming_dir, rpm_name)
        log.log(5, 'Pending RPM is: %s', pending_rpm)

        if 'job' not in params:
            params['job'] = application.path

        self._queue_rpm(pending_rpm, rpm_name, package, params['job'])

        # Wait until status has been updated to 'failed' or 'completed',
        # or timeout occurs (meaning repository side failed, check logs there)

        log.info('Waiting for software repository server to update '
                 'deploy repo...')

        log.log(5, 'Setting up signal handler')
        signal.signal(signal.SIGALRM, processing_handler)
        signal.alarm(params['package_add_timeout'])

        log.log(5, 'Waiting for status update in database for package')
        self.wait_for_state_change(package)

        signal.alarm(0)

        return dict(result=dict(package=package))

    @validate('package')
    def delete(self, package, **params):
        """Delete a given version of a package for a given project"""

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
        """Show information for all existing packages in the software
           repository for requested projects (or all projects)
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
