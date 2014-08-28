"""Commands to support managing packages in the TDS system."""

import os.path
import socket
import signal
import time

import tagopsdb
import tagopsdb.exceptions
import tagopsdb.deploy.repo
import tagopsdb.deploy.deploy
import tagopsdb.deploy.package

import tds.authorize
import tds.model
import tds.utils

import logging

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
        'Please contact SiteOps for assistance.'
    )


class PackageController(BaseController):
    """Commands to manage packages for supported applications"""

    access_levels = {
        'list': 'environment',
        'add': 'environment',
        'delete': 'environment',
    }

    @staticmethod
    def check_package_state(pkg_info):
        """Check state of package in database"""

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

    @staticmethod
    def _queue_rpm(params, queued_rpm, rpm_name, app):
        """Move requested RPM into queue for processing"""

        # Verify required RPM exists and create hard link into
        # the incoming directory for the repository server to find
        build_base = params['repo']['build_base']
        src_rpm = os.path.join(build_base, app.path, rpm_name)
        log.log(5, 'Source RPM is: %s', src_rpm)

        log.info('Checking for existence of file "%s"...', src_rpm)

        if not os.path.isfile(src_rpm):
            log.info('File "%s" is not found in "%s"',
                     src_rpm, build_base)
            return False

        log.info('Build host "%s" built RPM successfully',
                 app.build_host)
        log.info('Linking RPM into incoming directory...')
        try:
            os.link(src_rpm, queued_rpm)
        except OSError as e:
            log.error(e)
            return False

        log.info('RPM successfully linked')
        return True

    @validate('project')
    def add(self, project, **params):
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
        pkg = tagopsdb.Package.get(name=pkg_loc.name)

        if pkg is not None:
            raise Exception(
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
                raise Exception(
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

    @validate('project')
    def delete(self, project, **params):
        """Delete a given version of a package for a given project"""

        log.debug(
            'Deleting version %s of the package for project "%s" '
            'from software repository', params['version'],
            project.name
        )

        pkg_info = dict(
            project=project.name,
            version=params['version'],
            revision='1'
        )

        if self.check_package_state(pkg_info) is None:
            raise Exception(
                'Package "%s@%s" does not exist',
                project.name, params['version']
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
    def list(self, projects, **params):
        """Show information for all existing packages in the software
           repository for requested projects (or all projects)
        """

        packages_sorted = sorted(
            tagopsdb.deploy.package.list_packages([x.name for x in projects] or None),
            key=lambda package: (package.created, package.version, package.revision)
        )

        return dict(result=packages_sorted)
