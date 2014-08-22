'''
Commands to manage config-type projects.
'''

import tagopsdb
import tagopsdb.deploy.repo
import tagopsdb.exceptions

import tds.authorize
import tds.exceptions
import tds.model
import tds.utils
# TODO: this should be a subclass of ApplicationController (or removed)
from .project import ProjectController
from .deploy import DeployController

import logging

log = logging.getLogger('tds')


class Config(DeployController):
    """Commands to manage deployments for supported config applications"""

    requires_tier_progression = False

    @tds.utils.debug
    def repush(self, params):
        'Repush a version of a config project. Same as `deploy redeploy`'
        super(Config, self).redeploy(params)

    @tds.utils.debug
    def revert(self, params):
        '''
        Revert to the previous version of a config project.
        Same as `deploy rollback`
        '''
        super(Config, self).rollback(params)


class ConfigController(Config):
    """Controller for the config command"""

    @staticmethod
    def verify_package_arch(arch):
        """Ensure architecture for package is supported"""

        table = tagopsdb.model.PackageLocation.__table__
        arches = table.columns['arch'].type.enums

        if arch not in arches:
            raise Exception(
                "Invalid architecture: %s. Should be one of: %s",
                arch,
                u', '.join(sorted(arches))
            )

    @tds.utils.debug
    def create(self, **params):
        # XXX: Replace this with a call
        # XXX: to ApplicationController(log).add(params)
        """Add a new config project to the system"""

        log.debug('Creating new config project')

        tds.authorize.verify_access(params['user_level'], 'admin')
        try:
            self.verify_package_arch(params['arch'])
        except Exception as exc:
            return dict(error=exc)

        existing_proj = tds.model.Project.get(name=params['project'])

        if existing_proj is not None:
            return dict(error=Exception(
                "Project already exists: %s", existing_proj.name
            ))

        try:
            log.debug('Adding config project to repository')

            # Project type matches project name
            tagopsdb.deploy.repo.add_app_location(
                params['project'],
                params['buildtype'],
                params['pkgname'],
                params['project'],
                params['pkgpath'],
                params['arch'],
                params['buildhost'],
                params['env_specific']
            )
        except tagopsdb.exceptions.RepoException as exc:
            log.error(exc)
            return dict(error=exc)

        tagopsdb.Session.commit()
        log.debug('Committed database changes')

        return dict(result=tds.model.Project.get(name=params['project']))

    def push(self, **params):
        'Push a new version of a config project. Same as `deploy promote`'
        try:
            return super(ConfigController, self).promote(**params)
        except Exception as exc:
            return dict(error=exc)

    @staticmethod
    def delete(params):
        """Remove a config project from the system"""
        return ProjectController().delete(**params)
