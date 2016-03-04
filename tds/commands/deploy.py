"""
Controller for 'deploy' commands.
"""

import time
import logging

from collections import OrderedDict

import tagopsdb
import tagopsdb.deploy.deploy as tagopsdb_deploy
import tds.deploy_strategy
import tds.exceptions
import tds.model
import tds.notifications

from .base import BaseController, validate as input_validate

log = logging.getLogger('tds')


def create_deployment(hosts, apptypes, **params):
    """
    Translate the common "params" argument into a Deployment instance.
    """

    return tds.model.DeployInfo(
        actor=tds.model.Actor(
            name=params.get('user'),
            groups=params.get('groups'),
        ),
        action=dict(
            command=params.get('command_name'),
            subcommand=params.get('subcommand_name'),
        ),
        project=dict(
            # TODO: deployments should be for projects, not packages
            name=params.get('package_name'),
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
        'rollback': 'environment',
        'restart': 'environment',
    }

    def __init__(self, config):
        """
        Set some basic attributes.
        """

        self.deployment = None
        self.deploy_hosts = set()
        self.deploy_tiers = set()
        self.application = None
        self.environment = None
        self.package = None
        self.user = None

        super(DeployController, self).__init__(config)

        self.create_deploy_strategy(
            self.app_config.get('deploy_strategy', 'salt')
        )

    def create_deploy_strategy(self, deploy_strat_name):
        """
        Create a deploy strategy and set it to self.deploy_strategy for use by
        restart command.
        """
        if deploy_strat_name == 'mco':
            cls = tds.deploy_strategy.TDSMCODeployStrategy
        elif deploy_strat_name == 'salt':
            cls = tds.deploy_strategy.TDSSaltDeployStrategy
        else:
            raise tds.exceptions.ConfigurationError(
                'Invalid deploy strategy: {strat}.'.format(
                    strat=deploy_strat_name
                )
            )

        self.deploy_strategy = cls(
            **self.app_config.get(deploy_strat_name, {})
        )

    def determine_availability(self, host, deployment=False):
        """
        Determine if a host is available for deployment.
        """
        if deployment:
            host_deps = tagopsdb.HostDeployment.find(host_id=host.host_id)
        else:
            host_deps = tagopsdb.HostDeployment.find(host_id=host.id)

        return all(
            dep.deployment.status not in ['inprogress', 'queued']
            for dep in host_deps
        )

    def display_output(self):
        """
        Create a queue, alphabetized by tier name and host name.
        The daemon will go through the tier deployments first, by name.
        And go through each tier's hosts, by name.
        And then go through all the individual non-tier host deployments, by
        name.
        Emulate that with a queue and then go through displaying the status for
        each item in the queue.
        If the currently displaying item is a tier deployment, go through
        displaying all its host deployments first and then display the final
        status for the tier deployment.
        """
        queue = list()
        tier_deps = sorted(
            self.deployment.app_deployments,
            key=lambda dep: dep.target.name,
        )
        host_deps = sorted(
            self.deployment.host_deployments,
            key=lambda dep: dep.host.name,
        )

        for tier_dep in tier_deps:
            queue.append(tier_dep)
            tier_host_deps = sorted(
                [dep for dep in self.deployment.host_deployments if
                 dep.host.app_id == tier_dep.app_id],
                key=lambda dep: dep.host.name,
            )
            queue.extend(tier_host_deps)
        for host_dep in host_deps:
            if not any(getattr(dep, 'host_id', None) is not None and
                       dep.host_id == host_dep.host_id for dep in queue):
                queue.append(host_dep)

        while queue:
            curr_item = queue[0]
            while curr_item.status not in ('inprogress', 'complete', 'ok',
                                           'failed', 'incomplete'):
                time.sleep(0.1)
                self._refresh(curr_item)
            curr_status = curr_item.status
            if getattr(curr_item, 'app_id', None) is not None:
                self._display_status(curr_item)
                while len(queue) > 1:
                    next_item = queue[1]
                    if getattr(next_item, 'app_id', None) is not None or \
                            next_item.host.app_id != curr_item.app_id:
                        break
                    while next_item.status not in ('inprogress', 'ok',
                                                   'failed'):
                        time.sleep(0.1)
                        self._refresh(next_item)
                    self._display_status(next_item)
                    if next_item.status == 'inprogress':
                        while next_item.status not in ('failed', 'ok'):
                            time.sleep(0.1)
                            self._refresh(next_item)
                        self._display_status(next_item)
                    queue.pop(1)
                self._refresh(curr_item)
                self._display_status(curr_item)
            else:
                self._display_status(curr_item, True)
                while curr_item.status not in ('failed', 'ok'):
                    time.sleep(0.1)
                    self._refresh(curr_item)
                if curr_status != curr_item.status:
                    self._display_status(curr_item, True)
            queue.pop(0)
        self._refresh(self.deployment)
        log.info('Deployment:\t[{status}]'.format(
            status=self.deployment.status
        ))

    def _refresh(self, obj):
        """
        WTF
        """
        tagopsdb.Session.commit()
        obj.refresh()

    def _display_status(self, dep, host_only=False):
        """
        Display the current status of a host or tier deployment.
        If host_only, don't indent for a host deployment being part of a tier
        deployment.
        """
        if host_only:
            log.info('{host_name}:\t\t[{status}]'.format(
                host_name=dep.host.name,
                status=dep.status,
            ))
            return
        if getattr(dep, 'app_id', None) is not None:
            log.info('{tier_name}:\t\t[{status}]'.format(
                tier_name=dep.target.name,
                status=dep.status,
            ))
        else:
            log.info('\t{host_name}:\t[{status}]'.format(
                host_name=dep.host.name,
                status=dep.status,
            ))

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
                if app_deployment.package != package.delegate:
                    break

                app_deployments[apptype.id] = (apptype.name, app_deployment)

        return app_deployments

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
        """
        Attach to the session and handle a KeyboardInterrupt by canceling the
        deployment if possible/reasonable. Inform user.
        """
        log.info('Deployment now being run, press Ctrl-C at any time to '
                 'cancel...')

        try:
            self.display_output()
        except KeyboardInterrupt:
            self._refresh(self.deployment)
            if self.deployment.status in ['pending', 'queued']:
                log.info('Deployment was still pending or queued, '
                         'canceling now.')
                self.deployment.status = 'canceled'
                tagopsdb.Session.commit()
            elif self.deployment.status == 'inprogress':
                log.info('Deployment was in progress, canceling now; '
                         'the installer daemon will stop after its current '
                         'host deployment is complete.')
                self.deployment.status = 'canceled'
                tagopsdb.Session.commit()
            elif self.deployment.status in ['complete', 'failed']:
                log.info('Deployment was already completed, nothing to do.')
            else:
                raise RuntimeError('Deployment state "%s" unexpected.'
                                   % self.deployment.status)

    def prepare_deployments(self, params):
        """
        Prepare deployments for a promote.
        """
        self.deployment = tds.model.Deployment.create(
            user=self.user,
            delay=params.get('delay', 0),
        )

        if self.deploy_hosts:
            self.prepare_host_deployments()
        else:
            self.prepare_tier_deployments()

        tagopsdb.Session.commit()

    def prepare_host_deployments(self, hosts=None):
        """
        Prepare host deployments for a promote.
        """
        hosts_to_do = []

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
            tds.model.HostDeployment.create(
                deployment_id=self.deployment.id,
                host_id=host.id,
                user=self.user,
                status='pending',
                package_id=self.package.id
            )

    def prepare_tier_deployments(self):
        """
        Prepare tier deployments for a promote.
        """
        for tier in self.deploy_tiers:
            host_targets = list()
            for host in tier.hosts:
                if host.environment_id != self.environment.id:
                    continue
                latest_host_dep = \
                    self.application.get_latest_completed_host_deployment(
                        host.id
                    )
                if latest_host_dep and latest_host_dep.package_id == \
                        self.package.id:
                    continue
                host_targets.append(host)
            self.prepare_host_deployments(host_targets)
            tds.model.AppDeployment.create(
                deployment_id=self.deployment.id,
                app_id=tier.id,
                user=self.user,
                environment_id=self.environment.id,
                status='pending',
                package_id=self.package.id,
            )

    def perform_validation(self, app_deployment, package, params):
        """
        Perform validation on a given app deployment.
        """
        app_deployment.status = 'validated'
        tagopsdb.Session.commit()

        tagopsdb_deploy.delete_host_deployments(
            package.name,
            app_deployment.app_id,
            self.envs[params['env']]
        )

    def send_notifications(self, **params):
        """
        Send notifications for a given deployment.
        """
        deployment = create_deployment(
            hosts=self.deploy_hosts,
            apptypes=self.deploy_tiers,
            **params
        )

        notification = tds.notifications.Notifications(self.app_config)
        notification.notify(deployment)

    @input_validate('package_hostonly')
    @input_validate('targets')
    @input_validate('application')
    def fix(self, application, package, hosts=None, apptypes=None, **params):
        """
        Perform a deploy fix.
        """
        self.environment = tagopsdb.Environment.get(
            environment=self.envs[params['env']]
        )
        self.package = package
        self.application = application
        self.user = params['user']

        app_ids = set()
        self.deploy_tiers = set()
        host_ids = set()
        self.deploy_hosts = set()
        if hosts:
            for host in hosts:
                if host.id in host_ids:
                    continue
                ongoing_host_deps =  host.get_ongoing_deployments()
                if ongoing_host_deps:
                    log.info(
                        'User {user} is currently running a deployment for the'
                        ' host {host} in the {env} environment. Skipping...'
                        .format(
                            user=ongoing_host_deps[0].user,
                            host=ongoing_host_deps[0].host.name,
                            env=self.environment.environment,
                        )
                    )
                    continue
                ongoing_tier_deps =  host.application.get_ongoing_deployments(
                    self.environment.id
                )
                if ongoing_tier_deps:
                    log.info(
                        'User {user} is currently running a deployment for the'
                        ' tier {tier} in the {env} environment. Skipping...'
                        .format(
                            user=ongoing_tier_deps[0].user,
                            tier=host.application.name,
                            env=self.environment.environment,
                        )
                    )
                    continue
                found = application.get_latest_host_deployment(host.id)
                if not found:
                    log.info(
                        'No deployment of this application to host {h_name} '
                        'was found. Skipping....'.format(h_name=host.name)
                    )
                    continue
                elif found.status == 'ok':
                    log.info(
                        'Most recent deployment of this package on host '
                        '{h_name} was completed successfully. Skipping....'
                        .format(h_name=host.name)
                    )
                    continue
                host_ids.add(found.host_id)
                self.deploy_hosts.add(host)

        else:
            for apptype in apptypes:
                found = application.get_latest_tier_deployment(
                    apptype.id,
                    self.environment.id,
                )
                if not found:
                    log.info(
                        'No deployment of this application to tier {t_name} '
                        'was found. Skipping....'.format(t_name=apptype.name)
                    )
                    continue
                ongoing_tier_deps = apptype.get_ongoing_deployments(
                    self.environment.id
                )
                ongoing_host_deps = apptype.get_ongoing_host_deployments(
                    self.environment.id
                )
                if ongoing_tier_deps:
                    log.info(
                        'User {user} is currently running a deployment for the'
                        ' tier {tier} in the {env} environment. Skipping...'
                        .format(
                            user=ongoing_tier_deps[0].user,
                            tier=apptype.name,
                            env=self.environment.environment,
                        )
                    )
                    continue
                if ongoing_host_deps:
                    log.info(
                        'User {user} is currently running a deployment for the'
                        ' host {host} in the {env} environment. Skipping...'
                        .format(
                            user=ongoing_host_deps[0].user,
                            host=ongoing_host_deps[0].host.name,
                            env=self.environment.environment,
                        )
                    )
                    continue
                found = tds.model.AppDeployment(delegate=found)
                if found.status not in ('incomplete', 'pending'):
                    log.info(
                        'Most recent deployment of this package on tier '
                        '{t_name} was completed successfully. '
                        'Skipping....'.format(
                            t_name=apptype.name,
                        )
                    )
                    continue
                app_ids.add(found.app_id)
                self.deploy_tiers.add(apptype)
                host_ids |= set([
                    x.host_id for x in found.get_incomplete_host_deployments()
                ])

        if not (app_ids or host_ids):
            log.info('Nothing to do.')
            return dict()
        self.deployment = tds.model.Deployment.create(
            user=params['user'],
            status='pending',
            delay=params.get('delay', 0),
        )
        for app_id in app_ids:
            tds.model.AppDeployment.create(
                deployment_id=self.deployment.id,
                app_id=app_id,
                environment_id=self.environment.id,
                user=params['user'],
                package_id=package.id,
                status='pending',
            )
        for host_id in host_ids:
            tds.model.HostDeployment.create(
                deployment_id=self.deployment.id,
                host_id=host_id,
                user=params['user'],
                package_id=package.id,
                status='pending',
            )

        params['package_name'] = application.name
        params['version'] = package.version
        self.send_notifications(**params)

        self.deployment.status = 'queued'
        tagopsdb.Session.commit()
        if params['detach']:
            log.info('Deployment ready for installer daemon, disconnecting '
                     'now.')
            return dict()
        self.manage_attached_session()

    @input_validate('package')
    @input_validate('targets')
    @input_validate('application')
    def invalidate(self, application, package, hosts=None, apptypes=None,
                   **params):
        """
        Ensure that, for the tiers we're checking, the given package
        had been deployed at some point and is in the 'validated' state.
        If so, update tier to 'invalidated', otherwise do nothing
        (and mention nothing has been done).
        """
        app_deployments = self.find_current_app_deployments(
            package, apptypes, params
        )

        for apptype in apptypes:
            tier_name, curr_app_dep = app_deployments[apptype.id]

            if (curr_app_dep is not None and
                curr_app_dep.package == package.delegate):
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
        """
        For the given hosts for tiers, ensure the given package is not
        currently deployed (do nothing if this is the case), then attempt
        the deployments.... okay, this one is really complicated, let's
        discuss this one more.
        """
        self.environment = tagopsdb.Environment.get(
            environment=self.envs[params['env']]
        )
        self.package = package
        self.application = application
        self.user = params['user']

        app_deployments = self.find_current_app_deployments(
            package, apptypes, params
        )
        previous_env = self.get_previous_env(params['env'])

        for apptype in apptypes:
            if (previous_env and
                not package.check_app_deployments(apptype, previous_env) and
                not params.get('force')):
                log.info(
                    'Application "{app}", version "{vers}" is not validated in'
                    ' the previous environment for tier "{tier}", '
                    'skipping...'.format(
                        app=application.name,
                        vers=package.version,
                        tier=apptype.name
                    )
                )
                continue

            ongoing_deps = apptype.get_ongoing_deployments(self.environment.id)
            if ongoing_deps:
                log.info(
                    'User {user} is currently running a deployment for the '
                    'tier {tier} in the {env} environment. Skipping...'.format(
                        user=ongoing_deps[0].user,
                        tier=apptype.name,
                        env=self.environment.environment,
                    )
                )
                continue

            tier_name, curr_app_dep = app_deployments[apptype.id]

            if (curr_app_dep is not None and
                curr_app_dep.package == package.delegate):
                log.info(
                    'Application "{app}", version "{vers}" is currently '
                    'deployed on tier "{tier}", skipping...'.format(
                        app=application.name,
                        vers=package.version,
                        tier=tier_name
                    )
                )
                continue

            ongoing_host_deps = apptype.get_ongoing_host_deployments(
                self.environment.id
            )

            if hosts:
                app_hosts = set(host for host in hosts if host.app_id ==
                                apptype.id and host.environment_id ==
                                self.environment.id)

                to_remove = set()
                if ongoing_host_deps:
                    for host in app_hosts:
                        relevant_deps = [dep for dep in ongoing_host_deps if
                                         dep.host_id == host.id]
                        if relevant_deps:
                            log.info(
                                'User {user} is currently running a deployment'
                                ' for the host {host} in the {env} '
                                'environment. Skipping...'.format(
                                    user=relevant_deps[0].user,
                                    host=host.name,
                                    env=self.environment.environment,
                                )
                            )
                            to_remove.add(host)
                app_hosts -= to_remove

                self.deploy_hosts |= app_hosts
            elif ongoing_host_deps:
                log.info(
                    'User {user} is currently running a deployment for the '
                    'host {host} in the {env} environment. Skipping...'.format(
                        user=ongoing_host_deps[0].user,
                        host=ongoing_host_deps[0].host.name,
                        env=self.environment.environment,
                    )
                )
                continue
            else:
                self.deploy_tiers.add(apptype)

        if not (self.deploy_hosts or self.deploy_tiers):
            log.info('Nothing to do.')
            return dict()

        params['package_name'] = application.name
        self.prepare_deployments(params)
        self.send_notifications(**params)

        # Let installer daemon access deployment now
        self.deployment.status = 'queued'
        tagopsdb.Session.commit()

        if params['detach']:
            log.info('Deployment ready for installer daemon, disconnecting '
                     'now.')
            return dict()

        self.manage_attached_session()

    @input_validate('package')
    @input_validate('targets')
    @input_validate('application')
    def restart(self, application, package, hosts=None, apptypes=None,
                **params):
        """
        For the given hosts or tiers, restart the appropriate service
        on each one for the given package and inform if restart succeeded
        or failed.
        """
        self.environment = tagopsdb.Environment.get(
            environment=self.envs[params['env']]
        )

        restart_targets = list()

        if hosts:
            for host in hosts:
                dep = application.get_latest_host_deployment(host.id)
                if not dep:
                    dep = application.get_latest_tier_deployment(
                        host.app_id,
                        self.environment.id,
                    )
                    if not dep or dep.status in ('incomplete', 'inprogress'):
                        continue

                restart_targets.append((host, dep.package))
        elif apptypes:
            for apptype in apptypes:
                dep = application.get_latest_tier_deployment(
                    apptype.id,
                    self.environment.id,
                )
                if not dep or dep.status in ('incomplete', 'inprogress'):
                    continue

                found_host = False
                for host in apptype.hosts:
                    if host.environment_id == self.environment.id:
                        found_host = True
                        restart_targets.append((host, dep.package))

                if not found_host:
                    log.info(
                        'No hosts for tier {tier} in environment {env}. '
                        'Continuing...'.format(
                            tier=apptype.name,
                            env=self.environment.environment,
                        )
                    )


        if not restart_targets:
            raise tds.exceptions.InvalidOperationError(
                'Nothing to restart for application {app} in {env} '
                'environment.'.format(
                    app=package.name,
                    env=self.environment.environment,
                )
            )

        restart_targets.sort(key=lambda x: (x[0].name, x[1].name))

        restart_results = dict()

        delay = params.get('delay', None)
        for i, (host, pkg) in enumerate(restart_targets):
            success, restart_result = self.deploy_strategy.restart_host(
                host.name, pkg.name
            )

            log.info(
                '{hostname}:\t\t[{status}]{printout}'.format(
                    hostname=host.name,
                    status='success' if success else 'failed',
                    printout='' if success else '\n' + restart_result,
                )
            )

            if delay is not None and (i + 1) < len(restart_targets):
                time.sleep(delay)

        return dict()

    @input_validate('package')
    @input_validate('targets')
    @input_validate('application')
    def rollback(self, application, package, hosts=None, apptypes=None,
                 **params):
        """
        For the given hosts or tiers, ensure the package is installed.
        If so, determine the previous deployed and validated version;
        if there's one, install that version and for a tier rollback
        set the status to 'invalidated' (nothing for hosts), else throw
        appropriate error.  If no previous validated version, throw
        appropriate error as well.
        """
        self.environment = tagopsdb.Environment.get(
            environment=self.envs[params['env']]
        )
        self.package = package
        self.application = application
        self.user = params['user']

        host_deps = set()  # [(host_id, pkg_id), ...]
        self.deploy_hosts = set()
        tier_deps = set()  # [(tier_id, pkg_id), ...]
        self.deploy_tiers = set()
        tier_deps_to_invalidate = set()
        if hosts:
            for host in hosts:
                current_dep = application.get_latest_completed_host_deployment(
                    host_id=host.id,
                )
                current_tier_dep = \
                    application.get_latest_completed_tier_deployment(
                        tier_id=host.app_id,
                        environment_id=self.environment.id,
                    )
                if not current_dep or current_tier_dep.realized > \
                        current_dep.realized:
                    current_dep = current_tier_dep
                validated_dep = \
                    application.get_latest_completed_tier_deployment(
                        tier_id=host.app_id,
                        environment_id=self.environment.id,
                        must_be_validated=True,
                        exclude_package_ids=[current_dep.package_id],
                    )
                if not validated_dep:
                    log.info(
                        'No validated tier deployment for application {a_name}'
                        ' on tier {t_name} of host {h_name} before currently '
                        'deployed version. Skipping....'
                        .format(
                            a_name=application.name,
                            t_name=host.application.name,
                            h_name=host.name,
                        )
                    )
                    continue
                if host.get_ongoing_deployments():
                    log.info(
                        'There is an ongoing deployment for the host {h_name}.'
                        ' Skipping....'.format(h_name=host.name)
                    )
                    continue
                if host.application.get_ongoing_deployments(
                    self.environment.id
                ):
                    log.info(
                        'There is an ongoing deployment for the tier {t_name} '
                        'of the host {h_name} in the current environment. '
                        'Skipping....'.format(
                            t_name=host.application.name,
                            h_name=host.name,
                        )
                    )
                    continue
                host_deps.add((host.id, validated_dep.package_id))
                self.deploy_hosts.add(host)
        else:
            for apptype in apptypes:
                current_dep = application.get_latest_completed_tier_deployment(
                        tier_id=apptype.id,
                        environment_id=self.environment.id,
                    )
                validated_dep = \
                    application.get_latest_completed_tier_deployment(
                        tier_id=apptype.id,
                        environment_id=self.environment.id,
                        must_be_validated=True,
                        exclude_package_ids=[current_dep.package_id],
                    )
                if not validated_dep:
                    log.info(
                        'No validated tier deployment for application {a_name}'
                        ' on tier {t_name} before currently deployed version. '
                        'Skipping....'.format(
                            a_name=application.name,
                            t_name=apptype.name,
                        )
                    )
                    continue
                tier_deps.add((apptype.id, validated_dep.package_id))
                self.deploy_tiers.add(apptype)
                for host in tds.model.HostTarget.find(
                    app_id=apptype.id,
                    environment_id=self.environment.id,
                ):
                    host_deps.add((host.id, validated_dep.package_id))
                for invalid_dep in tds.model.AppDeployment.find(
                    app_id=current_dep.app_id,
                    environment_id=current_dep.environment_id,
                    package_id=current_dep.package_id,
                ):
                    tier_deps_to_invalidate.add(invalid_dep)
        if not (tier_deps or host_deps):
            log.info('Nothing to do.')
            return dict()
        self.deployment = tds.model.Deployment.create(
            user=params['user'],
            status='pending',
            delay=params.get('delay', 0),
        )
        for tier_dep in tier_deps:
            tds.model.AppDeployment.create(
                deployment_id=self.deployment.id,
                app_id=tier_dep[0],
                environment_id=self.environment.id,
                user=params['user'],
                package_id=tier_dep[1],
                status='pending',
            )
        for host_dep in host_deps:
            tds.model.HostDeployment.create(
                deployment_id=self.deployment.id,
                host_id=host_dep[0],
                user=params['user'],
                package_id=host_dep[1],
                status='pending',
            )

        params['package_name'] = application.name
        params['version'] = package.version
        self.send_notifications(**params)

        self.deployment.status = 'queued'
        for invalid_dep in tier_deps_to_invalidate:
            invalid_dep.status = 'invalidated'
            tagopsdb.Session.add(invalid_dep)
            for host_dep in invalid_dep.deployment.host_deployments:
                if host_dep.host.app_id != invalid_dep.app_id:
                    continue
                tagopsdb.Session.delete(host_dep)
        tagopsdb.Session.commit()
        if params['detach']:
            log.info('Deployment ready for installer daemon, disconnecting '
                     'now.')
            return dict()

        self.manage_attached_session()

    @input_validate('package_show')
    @input_validate('targets')
    @input_validate('application')
    def show(self, application, package, apptypes=None, **params):
        """
        For the given application/package and given apptypes,
        return the current deployment information (if any).
        """
        if not apptypes:
            apptypes = application.targets

        env_id = tagopsdb.Environment.get(
            environment=self.envs[params['env']],
        ).id
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
                application.get_latest_completed_tier_deployment(
                    tier_id=target.id,
                    environment_id=env_id,
                )
            previous_app_deployment = None
            package_id = package.id

            if params.get('version') is None:
                if current_app_deployment is not None:
                    previous_app_deployment = \
                        application.get_latest_completed_tier_deployment(
                            tier_id=target.id,
                            environment_id=env_id,
                            must_be_validated=True,
                            exclude_package_ids=[
                                current_app_deployment.package_id
                            ],
                        )
                package_id = None

            host_deployments = \
                application.get_latest_completed_host_deployments_for_tier(
                    tier_id=target.id,
                    environment_id=env_id,
                    package_id=package_id,
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
        """
        Ensure that, for the tiers we're checking, the given package is the
        current deployment and that the tier is in 'complete' state.
        If so, verify all the hosts have deployments in 'ok' state.
        If so, update tier to 'validated' and remove host deployments.
        Otherwise, throw appropriate error.
        """
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
