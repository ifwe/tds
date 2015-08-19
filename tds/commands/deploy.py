"""
Controller for 'deploy' commands.
"""

import logging

from .base import BaseController, validate as input_validate

log = logging.getLogger('tds')


class DeployController(BaseController):
    """
    Commands to manage deployments.
    """

    dep_types = {'promote': 'Deployment',
                 'fix': 'Fix',
                 'rollback': 'Rollback',
                 'push': 'Push',
                 'repush': 'Repush',
                 'revert': 'Reversion', }
    envs = {'dev': 'development',
            'stage': 'staging',
            'prod': 'production', }
    env_order = ['dev', 'stage', 'prod']

    requires_tier_progression = True

    access_levels = {
        'invalidate': 'environment',
        'show': 'environment',
        'validate': 'environment',
        'promote': 'environment',
        'fix': 'environment',
        'redeploy': 'environment',
        'rollback': 'environment',
        'restart': 'environment',
    }

    @input_validate('package_hostonly')
    @input_validate('targets')
    @input_validate('application')
    def fix(self, application, package, hosts=None, apptypes=None,
            **params):
        # For the given hosts or tiers, determine if there are any failed
        # host deployments.  If so, re-attempt the deployments after ensuring
        # no other conflicting deployments are in progress; if they
        # succeed and it's a tier deployment, update the tier as 'complete'
        # as well, otherwise leave as 'incomplete'.
        pass

    @input_validate('package')
    @input_validate('targets')
    @input_validate('application')
    def invalidate(self, application, package, hosts=None, apptypes=None,
                   **params):
        # Ensure that, for the tiers we're checking, the given package
        # had been deployed at some point and is in the 'validated' state.
        # If so, update tier to 'invalidated', otherwise do nothing
        # (and mention nothing has been done).
        pass

    @input_validate('package')
    @input_validate('targets')
    @input_validate('application')
    def promote(self, application, package, hosts=None, apptypes=None,
                **params):
        # For the given hosts for tiers, ensure the given package is not
        # currently deployed (do nothing if this is the case), then attempt
        # the deployments.... okay, this one is really complicated, let's
        # discuss this one more.
        pass

    @input_validate('package')
    @input_validate('targets')
    @input_validate('application')
    def restart(self, application, package, hosts=None, apptypes=None,
                **params):
        # For the given hosts or tiers, restart the appropriate service
        # on each one for the given package and inform if restart succeeded
        # or failed.
        pass

    @input_validate('package')
    @input_validate('targets')
    @input_validate('application')
    def rollback(self, application, package, hosts=None, apptypes=None,
                 **params):
        # For the given hosts or tiers, ensure the package is installed.
        # If so, determine the previous deployed and validated version;
        # if there's one, install that version and for a tier rollback
        # set the status to 'invalidated' (nothing for hosts), else throw
        # appropriate error.  If no previous validated version, throw
        # appropriate error as well.
        pass

    @input_validate('package_show')
    @input_validate('targets')
    @input_validate('application')
    def show(self, application, package, apptypes=None, **params):
        # For the given application/package and given apptypes,
        # return the current deployment information (if any).
        pass

    @input_validate('package')
    @input_validate('targets')
    @input_validate('application')
    def validate(self, application, package, hosts=None, apptypes=None,
                 **params):
        # Ensure that, for the tiers we're checking, the given package is the
        # current deployment and that the tier is in 'complete' state.
        # If so, verify all the hosts have deployments in 'ok' state.
        # If so, update tier to 'validated' and remove host deployments.
        # Otherwise, throw appropriate error.
        pass
