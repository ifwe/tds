'Commands to manage the deployment repository'
import logging

import tagopsdb.exceptions
import tagopsdb.deploy.package
import tagopsdb.deploy.repo

import tds.utils
from tds.model import Project

log = logging.getLogger('tds')


class Repository(object):

    """Commands to manage the deployment repository"""

    def __init__(self, logger=None):
        log.warning('Extra argument "logger" ignored in commands.repository')

    def add(self, params):
        """Add a given project to the repository"""

        log.debug('Adding application %r to repository',
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
            log.log(5, 'Application\'s Location ID is: %d',
                    project.id)

            log.debug('Mapping Location ID to various applications')
            tagopsdb.deploy.repo.add_app_packages_mapping(
                project,
                project_new,
                pkg_def,
                params['apptypes']
            )
        except tagopsdb.exceptions.RepoException as e:
            log.error(e)
            return

        if params['config']:
            # XXX: this should go away as config is not special
            log.debug('Adding application %r to config project %r',
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

                log.log(
                    5, 'Config project %r\'s Location ID is: %s',
                    params['config'], config.id
                )
                tagopsdb.deploy.repo.add_app_packages_mapping(
                    config,
                    config_new,
                    config_def,
                    params['apptypes']
                )
            except tagopsdb.exceptions.RepoException as e:
                log.error(e)
                return

        tagopsdb.Session.commit()
        log.debug('Committed database changes')

    @staticmethod
    @tds.utils.debug
    def delete(params):
        """Remove a given project from the repository"""

        log.debug('Removing application %r from repository',
                  params['project'])

        tds.authorize.verify_access(params['user_level'], 'admin')

        try:
            tagopsdb.deploy.repo.delete_app_location(params['project'])
        except tagopsdb.exceptions.RepoException as e:
            log.error(e)
            return

        tagopsdb.Session.commit()
        log.debug('Committed database changes')

    @staticmethod
    def list(*projects):
        """Show information for requested projects (or all projects)"""

        if projects:
            return dict(result=filter(None, [Project.get(name=p) for p in projects]))
        else:
            return dict(result=Project.all())
