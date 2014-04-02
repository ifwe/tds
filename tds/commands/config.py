'''
Commands to manage config-type projects.
'''
import elixir
import tagopsdb.deploy.repo
import tagopsdb.exceptions

import tds.utils
import tds.exceptions
from .repository import Repository
from .deploy import Deploy


class Config(Deploy):

    """Commands to manage deployments for supported config applications"""

    valid_project_types = ['tagconfig', 'kafka-config']
    requires_tier_progression = False

    @tds.utils.debug
    def create(self, params):
        # XXX: Replace this with a call to Repository(self.log).add(params)
        """Add a new config project to the system"""

        self.log.debug('Creating new config project')

        tds.authorize.verify_access(params['user_level'], 'admin')

        # Currently project type matches the project name
        if params['project'] not in self.valid_project_types:
            raise tds.exceptions.WrongProjectTypeError(
                'Project "%s" is not valid for this command',
                params['project']
            )

        try:
            self.log.debug(5, 'Adding config project to repository')

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
        except tagopsdb.exceptions.RepoException, e:
            self.log.error(e)
            return

        elixir.session.commit()
        self.log.debug('Committed database changes')

    @tds.utils.debug
    def delete(self, params):
        """Remove a config project from the system"""
        return Repository(self.log).delete(params)

    @tds.utils.debug
    def push(self, params):
        'Push a new version of a config project. Same as `deploy promote`'
        super(Config, self).promote(params)

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
