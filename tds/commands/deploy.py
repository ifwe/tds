"""
Controller for 'deploy' commands.
"""

import logging

import tagopsdb
import tagopsdb.deploy.deploy as tagopsdb_deploy

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

    def find_current_app_deployments(self, package, apptypes, params):
        """
        Given a specific package, determine current deployments of that
        package for a given set of apptypes in a given environment.
        """

        environment = tagopsdb.Environment.get(
            environment=self.envs[params['env']]
        )

        app_deployments = {}

        for apptype in apptypes:
            app_deployments[apptype.id] = (apptype.name, None)

            for app_deployment in apptype.app_deployments:
                if app_deployment.environment_obj != environment:
                    continue
                if app_deployment.deployment.package != package.delegate:
                    break

                app_deployments[apptype.id] = (apptype.name, app_deployment)

        return app_deployments

    def perform_validation(self, app_deployment, package, params):
        """
        Perform validation on a given app deployment
        """

        app_deployment.status = 'validated'
        tagopsdb.Session.commit()

        tagopsdb_deploy.delete_host_deployments(
            package.name,
            app_deployment.app_id,
            self.envs[params['env']]
        )

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
        app_deployments = self.find_current_app_deployments(
            package, apptypes, params
        )

        for apptype in apptypes:
            tier_name, curr_app_dep = app_deployments[apptype.id]

            if (curr_app_dep is not None and
                curr_app_dep.deployment.package == package.delegate):
                log.info('Application "%s", version "%s" is currently '
                         'deployed on tier "%s", skipping...',
                         application.name, package.version, tier_name)
                continue

            for app_deployment in package.app_deployments:
                if app_deployment.target in [x.delegate for x in apptypes]:
                    app_deployment.status = 'invalidated'

            tagopsdb.Session.commit()

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
        if not apptypes:
            apptypes = application.targets

        package_deployment_info = dict(
            package=package,
            environment=params['env'],
            by_apptype=[],
        )

        for target in apptypes:
            func_args = [
                package.name,
                self.envs[params['env']],
                target,
            ]

            current_app_deployment = \
                tagopsdb_deploy.find_specific_app_deployment(
                    *func_args, version=package.version
                )
            previous_app_deployment = None
            host_deployment_version = package.version

            if params.get('version') is None:
                previous_app_deployment = \
                    tagopsdb_deploy.find_previous_app_deployment(*func_args)
                host_deployment_version = None

            host_deployments = \
                tagopsdb_deploy.find_current_host_deployments(
                    *func_args, version=host_deployment_version
                )

            package_deployment_info['by_apptype'].append(
                dict(
                    apptype=target,
                    current_app_deployment=current_app_deployment,
                    previous_app_deployment=previous_app_deployment,
                    host_deployments=host_deployments,
                )
            )

        return dict(result=[package_deployment_info])

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
        app_deployments = self.find_current_app_deployments(
            package, apptypes, params
        )

        for apptype_id in app_deployments:
            tier_name, app_deployment = app_deployments[apptype_id]

            if app_deployment is None:
                log.info('Tier "%s" has no current deployment for '
                         'application "%s", version "%s" to validate',
                         tier_name, application.name, package.version)
                continue

            deploy_status = app_deployment.status

            if deploy_status == 'inprogress':
                log.info('Tier "%s" has a current deployment that is '
                         'in progress, skipping...', tier_name)
            elif deploy_status == 'validated':
                log.info('Tier "%s" has a current deployment that is '
                         'already validated, skipping...', tier_name)
            elif deploy_status in ['complete', 'invalidated']:
                self.perform_validation(app_deployment, package, params)
                log.info('Application "%s", version "%s" has been '
                         'validated on tier "%s"', application.name,
                         package.version, tier_name)
            elif deploy_status == 'incomplete':
                if params['force']:
                    self.perform_validation(app_deployment, package, params)
                    log.info('Application "%s", version "%s" has been '
                            'validated on tier "%s"', application.name,
                            package.version, tier_name)
                else:
                    log.info('Tier "%s" has a current deployment that is '
                             'incomplete, please use "--force" option to '
                             'override', tier_name)
