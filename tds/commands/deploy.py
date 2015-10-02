"""
Controller for 'deploy' commands.
"""

import logging

from collections import OrderedDict

import tagopsdb
import tagopsdb.deploy.deploy as tagopsdb_deploy
import tds.model
import tds.notifications

from .base import BaseController, validate as input_validate

log = logging.getLogger('tds')


def create_deployment(hosts, apptypes, **params):
    """
    Translate the common "params" argument into a Deployment instance.
    """

    return tds.model.Deployment(
        actor=tds.model.Actor(
            name=params.get('user'),
            groups=params.get('groups'),
        ),
        action=dict(
            command=params.get('command_name'),
            subcommand=params.get('subcommand_name'),
        ),
        package=tds.model.Package(
            name=params.get('package_name'),
            version=params.get('version'),
        ),
        target=dict(
            env=params.get('env'),
            apptypes=apptypes,
            hosts=hosts,
        ),
    )


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
    envs = OrderedDict([
        ('dev', 'development'),
        ('stage', 'staging'),
        ('prod', 'production'),
    ])
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

    def __init__(self, config):
        """"""

        self.deployment = None
        self.deployment_status = {}
        self.deploy_hosts = set()
        self.deploy_tiers = set()
        self.environment = None
        self.package = None
        self.user = None

        super(DeployController, self).__init__(config)

    def determine_availability(self, host, deployment=False):
        """"""

        if deployment:
            host_deps = tagopsdb.HostDeployment.find(host_id=host.host_id)
        else:
            host_deps = tagopsdb.HostDeployment.find(host_id=host.id)

        return all(
            dep.deployment.status not in ['inprogress', 'queued']
            for dep in host_deps
        )

    def display_output(self):
        """"""

        pass

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

    def fix_deployments(self):
        """"""

        self.deployment.status = 'pending'
        self.deployment_status['deployment'] = {
            self.deployment.id, self.deployment.status
        }

        if not self.deployment.app_deployments:
            self.deployment_status['type'] = 'host'
            host_deps = self.fix_host_deployments()

            if host_deps is None:
                tagopsdb.Session.rollback()
                # Log something, then return... something
            else:
                self.deployment_status['hosts'] = host_deps
        else:
            self.deployment_status['type'] = 'tier'
            tier_deps = self.fix_tier_deployments()

            if not tier_deps:
                tagopsdb.Session.rollback()
                # Log something, then return... something
            else:
                self.deployment_status['tiers'] = tier_deps

        tagopsdb.Session.commit()

    def fix_host_deployments(self, host_deps=None):
        """"""

        host_deps_to_do = []

        if host_deps is None:
            host_deps = self.deployment.host_deployments
            in_tier = False
        else:
            in_tier = True

        for host_dep in host_deps:
            available = self.determine_availability(host_dep, deployment=True)

            if not available:
                if in_tier:
                    return None
                else:  # Just remove host
                    continue
            else:
                if host_dep.status == 'failed':
                    host_deps_to_do.append(host_dep)

        if not host_deps_to_do:
            return None

        for host_dep in host_deps_to_do:
            host_dep.status = 'pending'

        return host_deps_to_do

    def fix_tier_deployments(self):
        """"""

        tier_deps = []

        self.deployment_status['hosts'] = []

        for tier_dep in self.deployment.app_deployments:
            host_deps = self.fix_host_deployments([
                host_dep for host_dep in self.deployment.host_deployments
                if host_dep.host.application == tier_dep.application
            ])

            if host_deps is None:
                continue   # Just remove tier
            else:
                self.deployment_status['hosts'].extend(host_deps)
                tier_dep.status = 'pending'
                tier_deps.append(tier_dep)

        return tier_deps

    def get_previous_env(self, env):
        """
        Find the previous environment (short name).
        Note this currently does NOT validate the environment name passed.
        """

        if env == 'dev':
            return None

        short_envs = self.envs.keys()
        return short_envs[short_envs.index(env) - 1]

    def manage_attached_session(self):
        """"""

        try:
            self.display_output()
        except KeyboardInterrupt:
            if self.deployment.status in ['pending', 'queued']:
                log.info('Deployment was still pending or queued, '
                         'canceling now.')
            elif self.deployment.status == 'inprogress':
                log.info('Deployment was in progress, canceling now; '
                         'the installer daemon will stop after its current '
                         'host deployment is complete.')
            elif self.deployment.status in ['complete', 'failed']:
                log.info('Deployment was already completed, nothing to do.')
                return
            else:
                raise RuntimeError('Deployment state "%s" unexpected'
                                   % self.deployment.status)

            self.deployment.status = 'canceled'
            tagopsdb.Session.commit()

    def prepare_deployments(self):
        """"""

        self.deployment = tds.model.Deployment.create(
            package_id=self.package.id, user=self.user
        )
        self.deployment_status['deployment'] = {
            self.deployment.id, self.deployment.status
        }

        if self.deploy_hosts:
            self.deployment_status['type'] = 'host'
            host_deps = self.prepare_host_deployments()

            if host_deps is None:
                tagopsdb.Session.rollback()
                # Log something, then return... something
            else:
                self.deployment_status['hosts'] = host_deps
        else:
            self.deployment_status['type'] = 'tier'
            tier_deps = self.prepare_tier_deployments()

            if not tier_deps:
                tagopsdb.Session.rollback()
                # Log something, then return... something
            else:
                self.deployment_status['tiers'] = tier_deps

        tagopsdb.Session.commit()

    def prepare_host_deployments(self, hosts=None):
        """"""

        hosts_to_do = []
        host_deps = []

        if hosts is None:
            hosts = self.deploy_hosts
            in_tier = False
        else:
            in_tier = True

        for host in hosts:
            available = self.determine_availability(host)

            if not available:
                if in_tier:
                    return None
                else:  # Just remove host
                    continue
            else:
                hosts_to_do.append(host)

        if not hosts_to_do:
            return None

        for host in hosts_to_do:
            host_dep = tds.model.HostDeployment.create(
                deployment_id=self.deployment.id,
                host_id=host.id,
                user=self.user,
                status='pending',
            )
            host_deps.append(host_dep)

        return host_deps

    def prepare_tier_deployments(self):
        """"""

        tier_deps = []

        self.deployment_status['hosts'] = []

        for tier in self.deploy_tiers:
            host_deps = self.prepare_host_deployments(tier.hosts)

            if host_deps is None:
                continue   # Just remove tier
            else:
                self.deployment_status['hosts'].extend(host_deps)
                tier_dep = tds.model.AppDeployment.create(
                    deployment_id=self.deployment.id,
                    app_id=tier.id,
                    user=self.user,
                    environment_id=self.environment.id,
                    status='pending',
                )
                tier_deps.append(tier_dep)

        return tier_deps

        #     for app_dep in tier.app_deployments:
        #         if app_dep.deployment.id == self.deployment.id:
        #             if app_dep.deployment.status in [
        #                 'incomplete', 'inprogress'
        #             ]:
        #                 tier_deps[app_dep.deployment.id] = \
        #                     app_dep.deployment.status = 'pending'
        #             elif app_dep.deployment.status in [
        #                 'complete', 'invalidated', 'validated'
        #             ]:
        #                 # Skip this tier
        #                 break
        #
        #             self.prepare_host_deployments(hosts=set(tier.hosts))
        #             break

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

    def send_notifications(self, **params):
        """Send notifications for a given deployment"""

        deployment = create_deployment(
            hosts=self.deploy_hosts,
            apptypes=self.deploy_tiers,
            **params
        )

        notification = tds.notifications.Notifications(self.app_config)
        notification.notify(deployment)

    @input_validate('deployment')
    def fix(self, deployment=None, **params):
        # For the given hosts or tiers, determine if there are any failed
        # host deployments.  If so, re-attempt the deployments after ensuring
        # no other conflicting deployments are in progress; if they
        # succeed and it's a tier deployment, update the tier as 'complete'
        # as well, otherwise leave as 'incomplete'.
        self.deployment = deployment

        if self.deployment.status not in ['failed', 'stopped']:
            log.info('Deployment %s not in failed state, nothing '
                     'to fix' % self.deployment.id)
            return dict()

        self.fix_deployments()
        self.send_notifications(**params)

        # Let installer daemon access deployment now
        self.deployment.status = 'queued'
        tagopsdb.Session.commit()

        if params['detach']:
            log.info('Deployment ready for installer daemon, disconnecting '
                     'now.')
            return dict()

        log.info('Deployment now being run, press Ctrl-C at any time to '
                 'cancel...')
        self.manage_attached_session()

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
        self.environment = tagopsdb.Environment.get(
            environment=self.envs[params['env']]
        )
        self.package = package
        self.user = params['user']

        app_deployments = self.find_current_app_deployments(
            package, apptypes, params
        )
        previous_env = self.get_previous_env(params['env'])

        for apptype in apptypes:
            if (previous_env and
                not package.check_app_deployments(apptype, previous_env) and
                not params.get('force')):
                log.info('Application "%s", version "%s" is not validated '
                         'in the previous environment for tier "%s", '
                         'skipping...', application.name, package.version,
                         apptype.name)
                continue

            tier_name, curr_app_dep = app_deployments[apptype.id]

            if (curr_app_dep is not None and
                curr_app_dep.deployment.package == package.delegate):
                log.info('Application "%s", version "%s" is currently '
                         'deployed on tier "%s", skipping...',
                         application.name, package.version, tier_name)
                continue

            if hosts:
                self.deploy_hosts.update(set(
                    host for host in hosts if host.application == apptype
                ))
            else:
                self.deploy_tiers.add(apptype)

        if not (self.deploy_hosts or self.deploy_tiers):
            return dict()

        self.prepare_deployments()
        self.send_notifications(**params)

        # Let installer daemon access deployment now
        self.deployment.status = 'queued'
        tagopsdb.Session.commit()

        if params['detach']:
            log.info('Deployment ready for installer daemon, disconnecting '
                     'now.')
            return dict()

        log.info('Deployment now being run, press Ctrl-C at any time to '
                 'cancel...')
        self.manage_attached_session()

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
        app_deployments = self.find_current_app_deployments(
            package, apptypes, params
        )

        for apptype in apptypes:
            tier_name, curr_app_dep = app_deployments[apptype.id]

            if hosts:
                self.deploy_hosts.update(set(
                    host for host in hosts if host.application == apptype
                ))

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
