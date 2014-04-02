'Commands to support managing packages in the TDS system'

import os.path
import socket
import signal
import time

import tagopsdb.exceptions
import elixir
import tagopsdb.deploy.repo
import tagopsdb.deploy.deploy
import tagopsdb.deploy.package

import tds.utils


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


class Package(object):

    """Commands to manage packages for supported applications"""

    def __init__(self, logger):
        """Basic initialization"""

        self.host = socket.gethostname()
        self.log = logger

    def check_package_state(self, pkg_info):
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
                self.log.info('Repository successfully updated')
                self.log.info('Added package for project "%s", version %s',
                              pkg_info['project'], pkg_info['version'])
                return
            elif pkg.status == 'failed':
                self.log.info('Failed to update repository with package '
                              'for project "%s", version %s',
                              pkg_info['project'], pkg_info['version'])
                self.log.info('Please try again')
                return
            else:
                if pkg.status != previous_status:
                    self.log.debug(5, 'State of package is now: %s',
                                   pkg.status)

                # The following line should reset the transaction
                # so the next query is re-read from the database
                elixir.session.remove()
                time.sleep(0.5)

    def _queue_rpm(self, params, queued_rpm, rpm_name, app):
        """Move requested RPM into queue for processing"""

        # Verify required RPM exists and create hard link into
        # the incoming directory for the repository server to find
        build_base = params['repo']['build_base']
        src_rpm = os.path.join(build_base, app.path, rpm_name)
        self.log.debug(5, 'Source RPM is: %s', src_rpm)

        self.log.info('Checking for existence of file "%s"...', src_rpm)

        if not os.path.isfile(src_rpm):
            self.log.info('File "%s" is not found in "%s"',
                          src_rpm, build_base)
            return False

        self.log.info('Build host "%s" built RPM successfully',
                      app.build_host)
        self.log.info('Linking RPM into incoming directory...')
        try:
            os.link(src_rpm, queued_rpm)
        except OSError as e:
            self.log.error(e)
            return False

        self.log.info('RPM successfully linked')
        return True

    @tds.utils.debug
    def add(self, params):
        """Add a given version of a package for a given project"""

        self.log.debug('Adding version %s of the package for project "%s" '
                       'to software repository', params['version'],
                       params['project'])

        tds.authorize.verify_access(params['user_level'], 'dev')

        # The real 'revision' is hardcoded to 1 for now
        # This needs to be changed at some point
        pkg_info = {'project': params['project'],
                    'version': params['version'],
                    'revision': '1', }

        if self.check_package_state(pkg_info) is None:
            try:
                tagopsdb.deploy.package.add_package(
                    params['project'],
                    params['version'],
                    '1',
                    params['user']
                )
            except tagopsdb.exceptions.PackageException as e:
                self.log.error(e)
                return

            elixir.session.commit()
            self.log.debug('Committed database changes')

            # Get repo information for package
            app = tagopsdb.deploy.repo.find_app_location(params['project'])

            # Revision hardcoded for now
            rpm_name = '%s-%s-1.%s.rpm' % (app.pkg_name, params['version'],
                                           app.arch)
            incoming_dir = params['repo']['incoming']

            pending_rpm = os.path.join(incoming_dir, rpm_name)
            self.log.debug(5, 'Pending RPM is: %s', pending_rpm)

            if not self._queue_rpm(params, pending_rpm, rpm_name, app):
                self.log.info('Failed to copy RPM into incoming directory')
                return

        # Wait until status has been updated to 'failed' or 'completed',
        # or timeout occurs (meaning repository side failed, check logs there)

        self.log.info('Waiting for software repository server to update '
                      'deploy repo...')

        self.log.debug(5, 'Setting up signal handler')
        signal.signal(signal.SIGALRM, processing_handler)
        signal.alarm(120)

        self.log.debug(5, 'Waiting for status update in database for package')
        self.wait_for_state_change(pkg_info)

        signal.alarm(0)

    @tds.utils.debug
    def delete(self, params):
        """Delete a given version of a package for a given project"""

        self.log.debug('Deleting version %s of the package for project "%s" '
                       'from software repository', params['version'],
                       params['project'])

        tds.authorize.verify_access(params['user_level'], 'dev')

        try:
            # The real 'revision' is hardcoded to 1 for now
            # This needs to be changed at some point
            tagopsdb.deploy.package.delete_package(
                params['project'],
                params['version'],
                '1'
            )
        except tagopsdb.exceptions.PackageException as e:
            self.log.error(e)
            return

        elixir.session.commit()
        self.log.debug('Committed database changes')

    @tds.utils.debug
    def list(self, params):
        """Show information for all existing packages in the software
           repository for requested projects (or all projects)
        """

        if params['projects'] is None:
            apps = 'ALL'
        else:
            apps = ', '.join(params['projects'])

        self.log.debug('Listing information for all existing packages '
                       'for projects: %s', apps)

        tds.authorize.verify_access(params['user_level'], 'dev')

        packages_sorted = sorted(
            tagopsdb.deploy.package.list_packages(params['projects']),
            key=lambda pkg: int(pkg.version)
        )

        for pkg in packages_sorted:
            self.log.info('Project: %s', pkg.pkg_name)
            self.log.info('Version: %s', pkg.version)
            self.log.info('Revision: %s', pkg.revision)
            self.log.info('')
