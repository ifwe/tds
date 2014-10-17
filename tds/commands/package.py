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

    @staticmethod
    def check_package_state(pkg_info):
        """Check state of package in database."""

        return tagopsdb.deploy.package.find_package(
            pkg_info['project'],
            pkg_info['version'],
            pkg_info['revision']
        )

    def wait_for_state_change(self, pkg_info):
        """Check for state change for package in database"""

        # This call is just to seed previous_status
        # for the first run of the loop
        pkg = self.check_package_state(pkg_info)

        while True:
            previous_status = pkg.status
            pkg = self.check_package_state(pkg_info)

            if pkg.status == 'completed':
                return pkg
            elif pkg.status == 'failed':
                log.info(
                    'Failed to update repository with package '
                    'for project "%s", version %s',
                    pkg_info['project'], pkg_info['version']
                )
                log.info('Please try again')
                return pkg
            else:
                if pkg.status != previous_status:
                    log.log(5, 'State of package is now: %s',
                            pkg.status)

                # The following line should reset the transaction
                # so the next query is re-read from the database
                tagopsdb.Session.remove()
                time.sleep(0.5)

    def _queue_rpm(self, params, queued_rpm, rpm_name, app):
        """Move requested RPM into queue for processing"""

        buildnum = int(params['version'])
        job_name = params['job_name']

        try:
            jenkins = jenkinsapi.jenkins.Jenkins(params['jenkins_url'])
        except Exception:
            raise tds.exceptions.FailedConnectionError(
                'Unable to contact Jenkins server "%s"',
                params['jenkins_url']
            )

        try:
            job = jenkins[job_name]
        except KeyError:
            raise tds.exceptions.NotFoundError('Job "%s" not found', job_name)

        try:
            build = job.get_build(buildnum)
        except (
            KeyError,
            JenkinsAPIException,
            NotFound
        ) as exc:
            log.error(exc)
            raise tds.exceptions.NotFoundError(
                'Build "%s@%s" does not exist on %s',
                params['job_name'],
                params['version'],
                params['jenkins_url']
            )

        try:
            artifacts = build.get_artifact_dict()[rpm_name]
            data = artifacts.get_data()
        except (
            KeyError,
            JenkinsAPIException,
            NotFound
        ):
            raise tds.exceptions.NotFoundError(
                'Artifact not found for "%s@%s" on %s',
                params['job_name'],
                params['version'],
                params['jenkins_url']
            )

        tmpname = os.path.join(os.path.dirname(os.path.dirname(queued_rpm)),
                               'tmp', rpm_name)

        for tmpfile in (tmpname, queued_rpm):
            tmpdir = os.path.dirname(tmpfile)
            if not os.path.isdir(tmpdir):
                os.makedirs(tmpdir)

        with open(tmpname, 'wb') as tmp_rpm:
            tmp_rpm.write(data)

        os.link(tmpname, queued_rpm)
        os.unlink(tmpname)

        return True

    @validate('project')
    def add(self, application, project, **params):
        """Add a given version of a package for a given project"""

        log.debug(
            'Adding version %s of the package for project "%s" '
            'to software repository', params['version'],
            project.name
        )

        # The real 'revision' is hardcoded to 1 for now
        # This needs to be changed at some point
        pkg_info = {'project': project.name,
                    'version': params['version'],
                    'revision': '1', }

        pkg_loc = tagopsdb.PackageLocation.get(app_name=project.name)
        pkg = tagopsdb.Package.get(
            name=pkg_loc.name, version=params['version']
        )

        if pkg is not None:
            raise tds.exceptions.AlreadyExistsError(
                'Package version "%s@%s" already exists',
                pkg.name, pkg.version
            )

        if self.check_package_state(pkg_info) is None:
            try:
                tagopsdb.deploy.package.add_package(
                    project.name,
                    params['version'],
                    '1',
                    params['user']
                )
            except tagopsdb.exceptions.PackageException as e:
                log.error(e)
                return

            tagopsdb.Session.commit()
            log.debug('Committed database changes')

            # Get repo information for package
            app = tagopsdb.deploy.repo.find_app_location(project.name)

            # Revision hardcoded for now
            rpm_name = '%s-%s-1.%s.rpm' % (app.pkg_name, params['version'],
                                           app.arch)
            incoming_dir = params['repo']['incoming']

            pending_rpm = os.path.join(incoming_dir, rpm_name)
            log.log(5, 'Pending RPM is: %s', pending_rpm)

            if not self._queue_rpm(params, pending_rpm, rpm_name, app):
                log.info('Failed to copy RPM into incoming directory')
                raise tds.exceptions.NotFoundError(
                    'Package "%s@%s" does not exist',
                    app.pkg_name, params['version']
                )

        # Wait until status has been updated to 'failed' or 'completed',
        # or timeout occurs (meaning repository side failed, check logs there)

        log.info('Waiting for software repository server to update '
                 'deploy repo...')

        log.log(5, 'Setting up signal handler')
        signal.signal(signal.SIGALRM, processing_handler)
        signal.alarm(params['package_add_timeout'])

        log.log(5, 'Waiting for status update in database for package')
        package = self.wait_for_state_change(pkg_info)

        signal.alarm(0)

        return dict(result=dict(
            project_name=project.name, package=package
        ))

    @validate('package')
    @validate('project')
    def delete(self, application, project, **params):
        """Delete a given version of a package for a given project"""

        log.debug(
            'Deleting version %s of the package for project "%s" '
            'from software repository', params['version'],
            project.name
        )

        try:
            # The real 'revision' is hardcoded to 1 for now
            # This needs to be changed at some point
            tagopsdb.deploy.package.delete_package(
                project.name,
                params['version'],
                '1'
            )
        except tagopsdb.exceptions.PackageException as e:
            log.error(e)
            return

        tagopsdb.Session.commit()
        log.debug('Committed database changes')

    @validate('project')
    def list(self, applications, projects, **params):
        """Show information for all existing packages in the software
           repository for requested projects (or all projects)
        """

        if not applications:
            applications = tds.model.Application.all()

        packages_sorted = sorted(
            tagopsdb.deploy.package.list_packages(
                [x.name for x in projects] or None
            ),
            key=lambda pkg: (pkg.name, pkg.created, pkg.version, pkg.revision)
        )

        return dict(result=packages_sorted)
