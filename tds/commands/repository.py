import tagopsdb.exceptions
import tagopsdb.deploy.package
import tagopsdb.deploy.repo

import tds.utils


class Repository(object):

    """Commands to manage the deployment repository"""

    def __init__(self, logger):
        """Basic initialization"""

        self.log = logger

    @tds.utils.debug
    def add(self, params):
        """Add a given project to the repository"""

        self.log.debug('Adding application %r to repository',
                       params['project'])

        tds.authorize.verify_access(params['user_level'], 'admin')

        try:
            # For now, project_type is 'application'
            params['projecttype'] = 'application'
            project, project_new, pkg_def = \
                tagopsdb.deploy.repo.add_app_location(
                    params['projecttype'],
                    params['buildtype'],
                    params['pkgname'],
                    params['project'],
                    params['pkgpath'],
                    params['arch'],
                    params['buildhost'],
                    params['env_specific']
                )
            self.log.debug(5, 'Application\'s Location ID is: %d',
                           project.id)

            self.log.debug('Mapping Location ID to various applications')
            tagopsdb.deploy.repo.add_app_packages_mapping(
                project,
                project_new,
                pkg_def,
                params['apptypes']
            )
        except tagopsdb.exceptions.RepoException as e:
            self.log.error(e)
            return

        if params['config']:
            # XXX: this should go away as config is not special
            self.log.debug('Adding application %r to config project %r',
                           params['project'], params['config'])

            try:
                config = tagopsdb.deploy.repo.find_app_location(
                    params['config']
                )
                # Transitional code for refactoring
                config_new = tagopsdb.deploy.repo.find_project(
                    params['config']
                )
                config_def = tagopsdb.deploy.package.find_package_definition(
                    config_new.id
                )

                self.log.debug(5, 'Config project %r\'s Location ID is: %s',
                               params['config'], config.id)
                tagopsdb.deploy.repo.add_app_packages_mapping(
                    config,
                    config_new,
                    config_def,
                    params['apptypes']
                )
            except tagopsdb.exceptions.RepoException as e:
                self.log.error(e)
                return

        tagopsdb.database.meta.Session.commit()
        self.log.debug('Committed database changes')

    @tds.utils.debug
    def delete(self, params):
        """Remove a given project from the repository"""

        self.log.debug('Removing application %r from repository',
                       params['project'])

        tds.authorize.verify_access(params['user_level'], 'admin')

        try:
            tagopsdb.deploy.repo.delete_app_location(params['project'])
        except tagopsdb.exceptions.RepoException as e:
            self.log.error(e)
            return

        tagopsdb.database.meta.Session.commit()
        self.log.debug('Committed database changes')

    @tds.utils.debug
    def list(self, params):
        """Show information for requested projects (or all projects)"""

        self.log.debug('Listing information for requested application(s) '
                       'in the repository')

        tds.authorize.verify_access(params['user_level'], 'dev')

        apps = tagopsdb.deploy.repo.list_app_locations(params['projects'])

        for app in apps:
            self.log.info('Project: %s', app.app_name)
            self.log.info('Project type: %s', app.project_type)
            self.log.info('Package type: %s', app.pkg_type)
            self.log.info('Package name: %s', app.pkg_name)
            self.log.info('Path: %s', app.path)
            self.log.info('Architecture: %s', app.arch)
            self.log.info('Build host: %s', app.build_host)

            self.log.debug(5, 'Finding application types for project "%s"',
                           app.app_name)
            app_defs = tagopsdb.deploy.repo.find_app_packages_mapping(
                app.app_name
            )
            app_types = sorted([x.app_type for x in app_defs])
            self.log.info('App types: %s', ', '.join(app_types))

            if app.environment:
                is_env = 'Yes'
            else:
                is_env = 'No'

            self.log.info('Environment specific: %s', is_env)
            self.log.info('')

        return apps
