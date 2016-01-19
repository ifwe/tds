"""
Controller for 'deploy' commands.
"""
import collections
import progressbar
import time
from datetime import datetime, timedelta

import tagopsdb
import tagopsdb.exceptions
import tagopsdb.deploy.repo
import tagopsdb.deploy.deploy
import tagopsdb.deploy.package

import tds.model
import tds.utils
import tds.notifications
import tds.exceptions
import tds.deploy_strategy

import logging

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

    """Commands to manage deployments for supported applications."""

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

    def __init__(self, config):
        """Basic initialization"""
        super(DeployController, self).__init__(config)

        self.create_deploy_strategy(
            self.app_config.get('deploy_strategy', 'mco')
        )

    def create_deploy_strategy(self, deploy_strat_name):
        if deploy_strat_name == 'mco':
            cls = tds.deploy_strategy.TDSMCODeployStrategy
        elif deploy_strat_name == 'salt':
            cls = tds.deploy_strategy.TDSSaltDeployStrategy
        else:
            raise tds.exceptions.ConfigurationError(
                'Invalid deploy strategy: %r', deploy_strat_name
            )

        self._deploy_strategy = cls(
            **self.app_config.get(deploy_strat_name, {})
        )

    @property
    def deploy_strategy(self):
        """
        Accessor for the DeployStrategy instance used by this object.
        """
        return self._deploy_strategy

    @tds.utils.debug
    def check_previous_environment(self, params, package, apptype):
        """Ensure deployment for previous environment for given package
           and apptier was validated; this is only relevant for staging
           and production environments.
        """
        # Note: this will currently allow any user to force
        # a deployment without previous tier requirement;
        # the use of '--force' needs to be authorized further up

        if not self.requires_tier_progression or params['force']:
            log.debug(
                'Previous environment not required for %r or "--force" '
                'option in use',
                package.name
            )
            return True

        log.debug('Checking for validation in previous environment')

        if params['env'] != 'dev':
            prev_env = self.get_previous_environment(params['env'])
            log.log(5, 'Previous environment is: %s', prev_env)

            prev_deps = tagopsdb.deploy.deploy.find_app_deployment(
                package.id,
                [apptype.id],
                self.envs[prev_env]
            )
            # There might be no deployment available; otherwise
            # there should only be one deployment here
            if not prev_deps:
                raise tds.exceptions.TDSException(
                    'Package "%s@%s" never validated in "%s" environment for '
                    'target "%s"',
                    package.name, params['version'],
                    prev_env, apptype.name
                )

            prev_app_dep, prev_app_type, prev_pkg = prev_deps[0]
            log.log(5, 'Previous application deployment is: %r',
                    prev_app_dep)
            log.log(5, 'Previous application type is: %s',
                    prev_app_type)
            log.log(5, 'Previous package is: %r', prev_pkg)

            if prev_app_dep.status != 'validated':
                log.info(
                    'Application %r with version %r not fully '
                    'deployed or validated to previous environment '
                    '(%s) for apptype %r', package.name,
                    params['version'], prev_env, prev_app_type
                )
                return False

        log.log(5, 'In development environment, nothing to check')

        return True

    @tds.utils.debug
    def check_for_current_deployment(self, params, apptype, hosts=[]):
        """For the current app type, see if there are any current
           deployments running and notify if there is.
        """

        log.debug(
            'Checking for a deployment of the same application '
            'already in progress'
        )

        time_delta = timedelta(hours=1)  # Harcoded to an hour for now
        log.log(5, 'time_delta is: %s', time_delta)

        dep = {}

        dep['info'] = tagopsdb.deploy.deploy.find_running_deployment(
            apptype.id,
            self.envs[params['env']],
            hosts=[x.name for x in hosts] if hosts else None
        )

        if dep['info']:
            log.debug('Current deployment found')

            dep['type'], data = dep['info']
            log.log(5, 'Deployment type is: %s', dep['type'])

            if dep['type'] == 'tier':
                dep['user'], dep['realized'], dep['env'], dep['apptype'] = \
                    data
                log.log(5, 'Deployment user is: %s', dep['user'])
                log.log(5, 'Deployment realized is: %s', dep['realized'])
                log.log(5, 'Deployment environment is: %s', dep['env'])
                log.log(5, 'Deployment apptype is: %s', dep['apptype'])

                if datetime.now() - dep['realized'] < time_delta:
                    log.info(
                        'User "%s" is currently running a '
                        'deployment for the %s app tier in the %s '
                        'environment, skipping...',
                        dep['user'], dep['apptype'], dep['env']
                    )
                    return True
            else:   # dep['type'] is 'host'
                dep['hosts'] = []

                for entry in data:
                    dep['user'], dep['realized'], dep['hostname'], \
                        dep['env'] = entry
                    log.log(5, 'Deployment user is: %s', dep['user'])
                    log.log(5, 'Deployment realized is: %s', dep['realized'])
                    log.log(5, 'Deployment hostname is: %s', dep['hostname'])
                    log.log(5, 'Deployment environment is: %s', dep['env'])

                    if datetime.now() - dep['realized'] < time_delta:
                        log.log(
                            5, 'Host %r active with deployment',
                            dep['hostname']
                        )
                        dep['hosts'].append(dep['hostname'])

                if dep['hosts']:
                    # Allow separate hosts to get simultaneous deployments
                    hosts = [host.name for host in hosts]
                    if (not hosts or
                            not set(dep['hosts']).isdisjoint(set(hosts))):
                        log.info(
                            'User "%s" is currently running a '
                            'deployment for the hosts "%s" in '
                            'the %s environment, skipping...',
                            dep['user'], ', '.join(dep['hosts']), dep['env']
                        )
                        return True

        log.debug('No current deployment found')
        return False

    @tds.utils.debug
    def check_tier_state(self, params, pkg, app_dep):
        """Ensure state of tier (from given app deployment) is consistent
           with state and deployment package versions.
        """

        log.debug('Checking state of tier')

        apptype_hosts = tagopsdb.deploy.deploy.find_hosts_for_app(
            app_dep.app_id,
            self.envs[params['env']]
        )
        apptype_hostnames = [x.hostname for x in apptype_hosts]
        log.log(5, 'Tier hosts are: %s', ', '.join(apptype_hostnames))

        dep_hosts = \
            tagopsdb.deploy.deploy.find_host_deployments_by_package_name(
                pkg.pkg_name,
                apptype_hostnames
            )
        dep_hostnames = [x.hostname for x in dep_hosts]

        if dep_hostnames:
            log.log(5, 'Deployed hosts are: %s', ', '.join(dep_hostnames))

        missing_deps = list(set(apptype_hostnames) - set(dep_hostnames))
        version_diffs = [x.hostname for x in dep_hosts
                         if x.version != params['version']]

        if version_diffs:
            log.log(5, 'Version differences on: %s', ', '.join(version_diffs))

        not_ok_hosts = tagopsdb.deploy.deploy.find_host_deployments_not_ok(
            pkg.id,
            app_dep.app_id,
            self.envs[params['env']]
        )
        not_ok_hostnames = [x.hostname for x in not_ok_hosts]

        if not_ok_hostnames:
            log.log(
                5, 'Hosts with failed deployments are: %s',
                ', '.join(not_ok_hostnames)
            )

        if missing_deps or version_diffs or not_ok_hosts:
            return ('failed', missing_deps, version_diffs, not_ok_hostnames)
        else:
            return ('ok', [], [], [])

    @tds.utils.debug
    def deploy_to_host(self, dep_host, app, version, retry=4):
        """Deploy specified package to a given host."""

        return self.deploy_strategy.deploy_to_host(
            dep_host,
            app,
            version,
            retry
        )

    @tds.utils.debug
    def restart_host(self, dep_host, app, retry=4):
        """Restart a host."""
        return self.deploy_strategy.restart_host(dep_host, app, retry)

    @tds.utils.debug
    def deploy_to_hosts(self, params, dep_hosts, dep, package_id,
                        redeploy=False):
        """Perform deployment on given set of hosts (only doing those
           that previously failed with a redeploy).
        """

        log.debug('Performing host deployments')

        total_hosts = len(dep_hosts)
        host_count = 1
        failed_hosts = []

        # widgets for progress bar
        widgets = ['Completed: ', progressbar.Counter(),
                   ' out of %d hosts' % total_hosts,
                   ' (', progressbar.Timer(), ', ', progressbar.ETA(), ')']

        if params.get('verbose', None) is None:
            pbar = progressbar.ProgressBar(widgets=widgets,
                                           maxval=total_hosts).start()

        pkg = tagopsdb.model.Package.get(id=package_id)
        app, version = pkg.name, pkg.version
        log.log(5, 'Application name and version: %s %s', app, version)

        for dep_host in sorted(dep_hosts, key=lambda host: host.hostname):
            host_dep = tagopsdb.model.HostDeployment.get(
                host_id=dep_host.id,
                package_id=pkg.id,
            )

            if redeploy and host_dep and host_dep.status != 'ok':
                log.log(5, 'Host %r needs redeloyment', dep_host.hostname)
                success, info = self.deploy_to_host(
                    dep_host.hostname, app, version
                )

                if success:
                    log.log(
                        5, 'Deployment to host %r successful',
                        dep_host.hostname
                    )

                    # Commit to DB immediately
                    host_dep.status = 'ok'
                    tagopsdb.Session.commit()

                    log.log(5, 'Committed database (nested) change')
                else:
                    log.log(
                        5, 'Deployment to host %r failed',
                        dep_host.hostname
                    )
                    failed_hosts.append((dep_host.hostname, info))
            else:
                if host_dep and host_dep.status == 'ok':
                    log.info(
                        'Host "%s" already has "%s@%s" successfully '
                        'deployed, skipping',
                        dep_host.hostname, app, version
                    )
                    continue

                # Clear out any old deployments for this host
                log.log(
                    5, 'Deleting any old deployments for host %r',
                    dep_host.hostname
                )
                tagopsdb.deploy.deploy.delete_host_deployment(
                    dep_host.hostname,
                    app
                )
                host_dep = tagopsdb.deploy.deploy.add_host_deployment(
                    dep.id,
                    dep_host.id,
                    params['user'],
                    'inprogress',
                    package_id,
                )
                success, info = self.deploy_to_host(dep_host.hostname, app,
                                                    version)

                if success:
                    log.log(
                        5, 'Deployment to host %r successful',
                        dep_host.hostname
                    )

                    # Commit to DB immediately
                    host_dep.status = 'ok'
                    tagopsdb.Session.commit()
                else:
                    log.log(
                        5, 'Deployment to host %r failed', dep_host.hostname
                    )

                    # Commit to DB immediately
                    host_dep.status = 'failed'
                    tagopsdb.Session.commit()

                    failed_hosts.append((dep_host.hostname, info))

                log.log(5, 'Committed database (nested) change')

            if params.get('verbose', None) is None:
                pbar.update(host_count)

            host_count += 1

            delay = params.get('delay', None)
            if delay is not None:
                log.log(5, 'Sleeping for %d seconds...', delay)
                time.sleep(delay)

        if params.get('verbose', None) is None:
            pbar.finish()

        # If any hosts failed, show failure information for each
        if failed_hosts:
            log.info('Some hosts had failures:\n')

            for failed_host, reason in failed_hosts:
                log.info('-----')
                log.info('Hostname: %s', failed_host)
                log.info('Reason: %s', reason)

            return False
        else:
            return True

    @tds.utils.debug
    def deploy_to_hosts_or_tiers(self, hosts, apptypes, params, dep,
                                 app_dep_map, package_id, redeploy=False,
                                 rollback=False):
        """Do the deployment to the requested hosts or application tiers"""

        log.debug('Deploying to requested hosts or application tiers')

        if hosts:
            log.log(5, 'Deployment is for hosts...')
            for apptype in list(apptypes):
                apphosts = [host for host in hosts
                            if host.target.id == apptype.id]
                if not apphosts:
                    continue

                if self.check_for_current_deployment(params, apptype,
                                                     hosts=apphosts):
                    log.log(
                        5, 'App %s already has deployment, skipping...',
                        apptype
                    )
                    apptypes.remove(apptype)
                    [hosts.remove(host) for host in hosts
                     if host.target.id == apptype.id]
                    continue

                log.log(5, 'Hosts being deployed to are: %r', apphosts)

                deploy_result = self.deploy_to_hosts(
                    params, apphosts, dep, package_id, redeploy=redeploy
                )

                if app_dep_map[apptype.id] is not None:
                    app_dep = app_dep_map[apptype.id][0]

                    if deploy_result:
                        # We want the tier status updated only if doing
                        # a rollback
                        if rollback:
                            app_dep.status = 'complete'
                        app_dep.deployment.status = 'complete'
                    else:
                        app_dep.deployment.status = 'failed'
        else:
            log.log(5, 'Deployment is for application tiers...')

            for apptype in list(apptypes):
                if apptype.id not in app_dep_map:
                    continue
                if self.check_for_current_deployment(params, apptype):
                    log.log(
                        5, 'App %s already has deployment, skipping...',
                        apptype
                    )
                    apptypes.remove(apptype)
                    app_dep_map.pop(apptype.id)
                    continue

                if redeploy:
                    dep_info = app_dep_map.get(apptype.id, None)
                    app_dep, app_type, pkg = dep_info

                    # Don't redeploy to a validated tier
                    if app_dep.status == 'validated':
                        log.info(
                            'Application "%s" with version "%s" '
                            'already validated on app type %s"',
                            pkg.name, pkg.version, app_type
                        )
                        continue
                else:
                    app_dep = tagopsdb.deploy.deploy.add_app_deployment(
                        dep.id,
                        apptype.id,
                        params['user'],
                        'inprogress',
                        self.envs[params['env']],
                        package_id,
                    )

                try:
                    dep_hosts = tagopsdb.deploy.deploy.find_hosts_for_app(
                        apptype.id,
                        self.envs[params['env']]
                    )
                except tagopsdb.exceptions.DeployException:
                    log.info(
                        'No hosts available for application type '
                        '"%s" in %s environment',
                        apptype.name, self.envs[params['env']]
                    )

                    # Set the deployment status due to no hosts
                    # being available
                    app_dep.status = 'incomplete'
                    log.log(
                        5, 'Setting deployment status to: %s', app_dep.status
                    )
                    continue

                if self.deploy_to_hosts(params, dep_hosts, dep, package_id,
                                        redeploy=redeploy):
                    app_dep.status = 'complete'
                    app_dep.deployment.status = 'complete'
                else:
                    app_dep.status = 'incomplete'
                    app_dep.deployment.status = 'failed'

                log.log(5, 'Setting deployment status to: %s', app_dep.status)

        if params['env'] == 'prod':
            log.info(
                'Please review the following Nagios group views '
                'or the deploy health status:'
            )

            for apptype in apptypes:
                log.info(
                    '  https://nagios.tagged.com/nagios/cgi-bin/'
                    'status.cgi?style=detail&hostgroup=app.%s', apptype.name
                )

    def determine_invalidations(self, application, params, apptypes,
                                app_dep_map):
        """Determine which application tiers need invalidations performed"""

        log.debug(
            'Determining invalidations for requested application types'
        )

        curr_deps = tagopsdb.deploy.deploy.find_latest_deployed_version(
            application.name,
            self.envs[params['env']],
            apptier=True
        )
        curr_dep_versions = {}

        for app_type, version, revision in curr_deps:
            log.log(
                5, 'App type: %s, Version: %s, Revision %s',
                app_type, version, revision
            )
            curr_dep_versions[app_type] = int(version)

        for apptype in apptypes:
            if not app_dep_map[apptype.id]:
                log.log(
                    5, 'Application ID %r is not in deployment/'
                    'application map', apptype.id
                )
                continue

            valid = True

            app_dep, app_type, pkg = app_dep_map[apptype.id]
            log.log(5, 'Application deployment is: %r', app_dep)
            log.log(5, 'Application type is: %s', app_type)
            log.log(5, 'Package is: %r', pkg)

            # Ensure version to invalidate isn't the current
            # deployment for this app type
            if curr_dep_versions.get(app_type, None) == params['version']:
                log.info(
                    'Unable to invalidate application "%s" with '
                    'version "%s" for apptype "%s" as that version '
                    'is currently deployed for the apptype',
                    application.name, params['version'], app_type
                )
                valid = False

            if valid:
                if app_dep.status != 'validated':
                    raise tds.exceptions.TDSException(
                        'Package "%s@%s" currently deployed on target "%s"',
                        pkg.name, pkg.version, app_type
                    )

            if not valid:
                log.log(
                    5, 'Deleting application ID %r from '
                    'deployment/application map', apptype.id
                )
                del app_dep_map[apptype.id]

        log.log(5, 'Deployment/application map is: %r', app_dep_map)

        return app_dep_map

    @tds.utils.debug
    def determine_new_deployments(self, hosts, apptypes, params, package,
                                  app_dep_map):
        """Determine which application tiers or hosts need new deployments"""

        log.debug(
            'Determining deployments for requested application '
            'types or hosts'
        )

        # For each app type, do the following:
        #   1. If app type does haven't a current deployment, check next
        #   2. For non-development environments, ensure the previous
        #      environment has a validated instance of the requested
        #      version of the application
        #   3. If step 2 is okay, check if the requested version of
        #      the application is already deployed and not invalidated
        #   4. If either step 2 or 3 failed, remove host/app type from
        #      relevant mapping to be used for deployments
        for apptype in apptypes:
            valid = self.check_previous_environment(
                params, package, apptype
            )

            if valid:
                if not app_dep_map[apptype.id]:
                    log.log(
                        5, 'Application %r is not in '
                        'deployment/application map', apptype
                    )
                    continue

                app_dep, app_type, pkg = app_dep_map[apptype.id]
                log.log(5, 'Application deployment is: %r', app_dep)
                log.log(5, 'Application type is: %s', app_type)
                log.log(5, 'Package is: %r', pkg)

                if (app_dep.status in ('validated', 'complete')
                    and pkg.version == params['version']):
                    log.info(
                        'Application "%s" with version "%s" '
                        'already deployed to this environment (%s) '
                        'for apptype "%s"',
                        package.name, params['version'],
                        self.envs[params['env']], app_type
                    )
                    valid = False

            if not valid:
                if hosts:
                    log.log(
                        5, 'Deleting hosts that belong to application %r',
                        apptype
                    )
                    [hosts.remove(host) for host in hosts
                     if host.target.id == apptype.id]
                else:
                    log.log(
                        5, 'Deleting application %r from '
                        'deployment/application map', apptype
                    )
                    del app_dep_map[apptype.id]

        log.log(5, 'Deployment/application map is: %r', app_dep_map)

        return app_dep_map

    @tds.utils.debug
    def determine_rollbacks(self, hosts, apptypes, params, app_dep_map):
        """Determine which application tiers or hosts need rollbacks"""

        log.debug('Determining rollbacks for requested application types')

        app_pkg_map = {}

        for apptype in apptypes:
            if app_dep_map.get(apptype.id, None) is None:
                log.log(
                    5, 'Application %r is not in '
                    'deployment/application map', apptype
                )
                continue

            valid = True

            _app_dep, app_name, package = app_dep_map[apptype.id]

            pkg_def = package.package_definition

            if hosts:
                prev_dep_info = \
                    tagopsdb.deploy.deploy.find_latest_validated_deployment(
                        pkg_def.name, apptype.id,
                        self.envs[params['env']])
            else:
                prev_dep_info = \
                    tagopsdb.deploy.deploy.find_previous_validated_deployment(
                        pkg_def.name, apptype.id,
                        self.envs[params['env']])

            if prev_dep_info is None:
                log.info(
                    'No previous deployment to roll back to for '
                    'application "%s" for app type "%s" in %s '
                    'environment', pkg_def.name, app_name,
                    self.envs[params['env']]
                )
                valid = False
            else:
                prev_app_dep, prev_pkg_id = prev_dep_info
                log.log(
                    5, 'Previous application deployment is: %r',
                    prev_app_dep
                )
                log.log(5, 'Previous package ID is: %s', prev_pkg_id)

                app_pkg_map[apptype.id] = prev_pkg_id

            if not valid:
                log.log(
                    5, 'Deleting application %r from '
                    'deployment/application map', apptype
                )
                del app_dep_map[apptype.id]

        log.log(5, 'Package/application map is: %r', app_pkg_map)
        log.log(5, 'Deployment/application map is: %r', app_dep_map)

        return (app_pkg_map, app_dep_map)

    @tds.utils.debug
    def determine_validations(self, params, apptypes, app_dep_map):
        """Determine which application tiers need validation performed"""

        for apptype in apptypes:
            if not app_dep_map[apptype.id]:
                log.log(
                    5, 'Application ID %r is not in '
                    'deployment/application map', apptype.id
                )
                continue

            valid = True

            app_dep, app_type, pkg = app_dep_map[apptype.id]
            log.log(5, 'Application deployment is: %r', app_dep)
            log.log(5, 'Application type is: %s', app_type)
            log.log(5, 'Package is: %r', pkg)

            if app_dep.status == 'validated':
                log.info(
                    'Deployment for application %r for apptype %r '
                    'already validated in %s environment',
                    pkg.name, app_type, self.envs[params['env']]
                )
                valid = False

            if valid:
                # Ensure tier state is consistent
                result, missing, diffs, not_ok_hostnames = \
                    self.check_tier_state(params, pkg, app_dep)

                if result != 'ok':
                    log.info(
                        'Encountered issues while validating '
                        'version %r of application %r:',
                        params['version'], pkg.name
                    )

                    if missing:
                        log.info(
                            '  Hosts missing deployments of given version:'
                        )
                        log.info('    %s', ', '.join(missing))

                    if diffs:
                        log.info(
                            '  Hosts with different versions than '
                            'the one being validated:'
                        )
                        log.info('    %s', ', '.join(diffs))

                    if not_ok_hostnames:
                        log.info('  Hosts not in an "ok" state:')
                        log.info('    %s', ', '.join(not_ok_hostnames))

                    if params['force']:
                        log.info(
                            'The "--force" option was used, '
                            'validating regardless'
                        )
                        valid = True
                    else:
                        log.info(
                            'Rejecting validation, please use '
                            '"--force" if you still want to validate'
                        )
                        valid = False

            if not valid:
                log.log(
                    5, 'Deleting application ID %r from '
                    'deployment/application map', apptype.id
                )
                del app_dep_map[apptype.id]

        log.log(5, 'Deployment/application map is: %r', app_dep_map)

        return app_dep_map

    @tds.utils.debug
    def find_app_deployments(self, package, apptypes, params):
        """Find all relevant application deployments for the requested
        app types and create an application/deployment mapping,
        keeping track of which app types have a current deployment
        and which don't
        """

        log.debug('Finding all relevant application deployments')

        environment = tagopsdb.Environment.get(
            environment=self.envs[params['env']]
        )

        app_deployments = {}

        for app in apptypes:
            app_deployments[app.id] = None

            for app_dep in app.app_deployments:
                if app_dep.environment_id != environment.id:
                    continue
                if app_dep.package_id != package.id:
                    continue

                app_deployments[app.id] = (
                    app_dep, app.name, package
                )
                break

        return app_deployments

    @tds.utils.debug
    def get_app_info(self, package, hosts, apptypes, params, hostonly=False):
        """Verify requested package and which hosts or app tiers
        to install the package
        """

        log.debug(
            'Verifying requested package is correct for given '
            'application tiers or hosts'
        )

        if hosts:
            log.log(5, 'Verification is for hosts...')

            host_deps = \
                tagopsdb.deploy.deploy.find_host_deployments_by_package_name(
                    package.name,
                    [x.name for x in hosts]
                )

            for host_dep, hostname, app_id, dep_version in host_deps:
                log.log(5, 'Host deployment is: %r', host_dep)
                log.log(5, 'Hostname is: %s', hostname)
                log.log(5, 'Application ID is: %s', app_id)
                log.log(5, 'Deployment version is: %s', dep_version)

                curr_version = params.get('version', dep_version)
                log.log(5, 'Current version is: %s', curr_version)

                if (params['subcommand_name'] != 'rollback'
                    and dep_version == curr_version
                        and host_dep.status == 'ok' and params['deployment']):
                    log.info(
                        'Application %r with version %r already '
                        'deployed to host %r', package.name,
                        curr_version, hostname
                    )
                    if hostname in hosts:
                        hosts.remove(hostname)

            apptypes = [host.target for host in hosts]

            apptypes = list(set(apptypes))
        else:
            log.log(5, 'Verification is for application tiers...')

            for apptype in apptypes:
                if not tagopsdb.Host.find(application=apptype):
                    raise tds.exceptions.InvalidOperationError(
                        ("No hosts are associated with the app tier '%s' in "
                         "the %s environment"),
                        apptype.name,
                        params['env'],
                    )

        log.log(5, 'Package ID is: %s', package.id)
        log.log(
            5, 'Application IDs are: %s',
            ', '.join([str(x.id) for x in apptypes])
        )

        return apptypes

    @tds.utils.debug
    def get_previous_environment(self, curr_env):
        """Find the previous environment to the current one"""

        log.debug('Determining previous deployment environment')

        # Done this way since negative indexes are allowed
        if curr_env == 'dev':
            raise tds.exceptions.WrongEnvironmentError(
                'There is no environment before the current environment (%s)',
                curr_env
            )

        try:
            return self.env_order[self.env_order.index(curr_env) - 1]
        except ValueError:
            raise tds.exceptions.WrongEnvironmentError(
                'Invalid environment: %s', curr_env
            )

    @tds.utils.debug
    def perform_deployments(self, hosts, apptypes, package, params,
                            app_dep_map):
        """Perform all deployments to the requested application tiers or
           hosts
        """
        log.debug('Performing deployments to application tiers or hosts')

        log.log(5, 'Creating new deployment')

        pkg_dep = tagopsdb.deploy.deploy.add_deployment(
            params['user'],
        )
        dep = pkg_dep
        log.log(5, 'Deployment is: %s', dep)

        self.deploy_to_hosts_or_tiers(
            hosts, apptypes, params, dep, app_dep_map, package.id
        )

    @staticmethod
    def perform_invalidations(app_dep_map):
        """Perform all invalidations to the requested application tiers"""

        log.debug('Performing invalidations to application tiers')

        for dep_info in app_dep_map.itervalues():
            app_dep, app_type, pkg = dep_info
            log.log(5, 'Application deployment is: %r', app_dep)
            log.log(5, 'Application type is: %s', app_type)
            log.log(5, 'Package is: %r', pkg)

            app_dep.status = 'invalidated'

    @tds.utils.debug
    def perform_redeployments(self, hosts, apptypes, params, deployment,
                              app_dep_map, package_id):
        """Perform all redeployments to the requested application tiers or
           hosts
        """

        log.debug('Performing redeployments to application tiers or hosts')

        self.deploy_to_hosts_or_tiers(
            hosts, apptypes, params, deployment, app_dep_map, package_id,
            redeploy=True
        )

    @tds.utils.debug
    def perform_rollbacks(self, hosts, apptypes, params, app_pkg_map,
                          app_dep_map):
        """Perform all rollbacks to the requested application tiers
           or hosts
        """

        log.debug('Performing rollbacks to application tiers or hosts')

        # Since a roll back could end up at different versions for
        # each application tier, must do each tier (or host(s) in
        # tier) on its own
        for app_id, pkg_id in app_pkg_map.iteritems():
            app_dep, app_type, pkg = app_dep_map[app_id]
            log.log(5, 'Application deployment is: %r', app_dep)
            log.log(5, 'Application type is: %s', app_type)
            log.log(5, 'Package is: %r', pkg)

            app_id = app_dep.app_id
            log.log(5, 'Application ID is: %s', app_id)

            if hosts:
                apphosts = [host for host in hosts
                            if host.target.id == app_id]
            else:
                apphosts = []

            if not apphosts:
                log.log(5, 'Creating new deployment')

                pkg_dep = tagopsdb.deploy.deploy.add_deployment(
                    params['user'],
                )
                dep = pkg_dep
                log.log(5, 'Deployment is: %s', dep)
            else:
                # Reset app deployment to 'inprogress' (if tier rollback)
                # or 'incomplete' (if host rollback), will require
                # revalidation
                if hosts:
                    app_dep.status = 'incomplete'
                else:
                    app_dep.status = 'inprogress'

                tagopsdb.Session.commit()

                dep = app_dep.deployment

            single_app_dep_map = {app_id: app_dep_map[app_id]}

            self.deploy_to_hosts_or_tiers(
                apphosts, apptypes, params, dep, single_app_dep_map, pkg_id,
                rollback=True
            )

    @tds.utils.debug
    def perform_validations(self, params, app_dep_map):
        """Perform all validations to the requested application tiers"""

        log.debug('Performing validations to application tiers')

        for dep_info in app_dep_map.itervalues():
            app_dep, app_type, pkg = dep_info
            log.log(5, 'Application deployment is: %r', app_dep)
            log.log(5, 'Application type is: %s', app_type)
            log.log(5, 'Package is: %r', pkg)

            # Commit to DB immediately
            app_dep.status = 'validated'
            tagopsdb.Session.commit()

            log.log(5, 'Committed database (nested) change')
            log.log(5, 'Clearing host deployments for application tier')
            tagopsdb.deploy.deploy.delete_host_deployments(
                pkg.name,
                app_dep.app_id,
                self.envs[params['env']]
            )

    @tds.utils.debug
    def send_notifications(self, hosts, apptypes, **params):
        """Send notifications for a given deployment"""

        log.debug('Sending notifications for given deployment')

        deployment = create_deployment(
            hosts=hosts,
            apptypes=apptypes,
            **params
        )

        notification = tds.notifications.Notifications(self.app_config)
        notification.notify(deployment)

    @input_validate('package')
    @input_validate('targets')
    @input_validate('application')
    def promote(self, application, package, hosts=None, apptypes=None,
                **params):
        """Deploy given version of given application to requested application
           tiers or hosts
        """
        log.debug('Deploying application')

        target_apptypes = self.get_app_info(package, hosts, apptypes, params)

        params['package_name'] = package.name

        app_dep_map = self.find_app_deployments(
            package, target_apptypes, params
        )
        app_dep_map = self.determine_new_deployments(
            hosts, target_apptypes, params, package, app_dep_map
        )

        if not (hosts or apptypes):
            return dict()

        self.send_notifications(
            hosts=hosts, apptypes=target_apptypes, **params
        )
        self.perform_deployments(
            hosts, target_apptypes, package, params, app_dep_map
        )

        tagopsdb.Session.commit()
        log.debug('Committed database changes')
        return dict()

    @input_validate('package')
    @input_validate('targets')
    @input_validate('application')
    def invalidate(self, application, package, hosts=None,
                   apptypes=None, **params):
        """Invalidate a given version of a given application"""

        log.debug('Invalidating for given application')
        # Not a deployment
        params['deployment'] = False

        apptypes = self.get_app_info(package, hosts, apptypes, params)

        app_dep_map = self.find_app_deployments(package, apptypes, params)

        if not len(list(filter(None, app_dep_map.itervalues()))):
            raise tds.exceptions.InvalidOperationError(
                'No deployments to invalidate for application %r '
                'with version %r in %s environment',
                package.name, params['version'],
                self.envs[params['env']]
            )

        app_dep_map = self.determine_invalidations(application, params,
                                                   apptypes, app_dep_map)
        self.perform_invalidations(app_dep_map)

        tagopsdb.Session.commit()
        log.debug('Committed database changes')
        return dict()

    @input_validate('package_show')
    @input_validate('targets')
    @input_validate('application')
    def show(self, application, package, apptypes=None, **params):
        """Show deployment information for a given application"""

        # TODO: showing project information (collection of applications)
        log.debug('Showing deployment information for given application')

        version = params.get('version', None)
        app_target_map = collections.defaultdict(list)

        if not apptypes:
            apptypes = application.targets

        # Note: eventually there may be multiple package definitions
        # for an given application name, which will need to be handled
        app_target_map[application] = [target for target in apptypes]

        # Find deployments
        deploy_info = []

        for app in app_target_map.keys():
            pkg_dep_info = dict(
                environment=params['env'],
                package=app,
                by_apptype=[],
            )

            for target in app_target_map[app]:
                func_args = [
                    app.name,
                    self.envs[params['env']],
                    target
                ]

                if version is None:
                    curr_app_dep = \
                        tagopsdb.deploy.deploy.find_current_app_deployment(
                            *func_args
                        )
                    prev_app_dep = \
                        tagopsdb.deploy.deploy.find_previous_app_deployment(
                            *func_args
                        )
                else:
                    curr_app_dep = \
                        tagopsdb.deploy.deploy.find_specific_app_deployment(
                            *func_args, version=version
                        )
                    prev_app_dep = None

                host_deps = \
                    tagopsdb.deploy.deploy.find_current_host_deployments(
                        *func_args, version=version
                    )

                pkg_dep_info['by_apptype'].append(dict(
                    apptype=target,
                    current_app_deployment=curr_app_dep,
                    previous_app_deployment=prev_app_dep,
                    host_deployments=host_deps,
                ))

            deploy_info.append(pkg_dep_info)

        return dict(result=deploy_info)

    @input_validate('package')
    @input_validate('targets')
    @input_validate('application')
    def rollback(self, application, package, hosts=None, apptypes=None,
                 **params):
        """Rollback to the previous validated deployed version of given
           application on requested application tiers or hosts
        """

        log.debug('Rolling back application')

        apptypes = self.get_app_info(package, hosts, apptypes, params)
        app_dep_map = self.find_app_deployments(package, apptypes, params)

        if not len(filter(None, app_dep_map.itervalues())):
            raise tds.exceptions.InvalidOperationError(
                'Nothing to roll back for application %r in %s '
                'environment', package.name,
                self.envs[params['env']]
            )

        # Save verison of application/deployment map for invalidation
        # at the end of the run
        log.log(5, 'Saving current application/deployment map')
        orig_app_dep_map = app_dep_map

        app_pkg_map, app_dep_map = \
            self.determine_rollbacks(hosts, apptypes, params, app_dep_map)

        # May need to change when 'package' has name removed (found
        # via 'package_definition')
        params['package_name'] = package.name
        params['version'] = package.version

        self.send_notifications(
            hosts, apptypes, application=application, **params
        )
        self.perform_rollbacks(
            hosts, apptypes, params, app_pkg_map, app_dep_map
        )

        if not hosts:
            # Now perform invalidations, commit immediately follows
            # Note this is only done for tiers
            self.perform_invalidations(orig_app_dep_map)

        tagopsdb.Session.commit()
        log.debug('Committed database changes')

        return dict()

    @staticmethod
    def get_package_for_target(target, environment):
        """
        Return the package for the given target in the given environment.
        """
        deployments = target.app_deployments
        dep = None
        for dep in sorted(deployments, key=lambda x: x.realized,
                          reverse=True):
            if dep.environment != environment.environment:
                continue

            if dep.status in ('inprogress', 'incomplete'):
                raise tds.exceptions.TDSException(
                    'Deploy target "%s" is being deployed to currently',
                    target.name
                )

            if dep.status in ('complete', 'validated'):
                break
        else:
            dep = None

        if dep is not None:
            pkg = dep.package
            return pkg

        return None

    @input_validate('package')
    @input_validate('targets')
    @input_validate('application')
    def restart(self, application, package, hosts=None, apptypes=None,
                **params):
        """Restart given application on requested tiers or hosts"""

        log.debug('Restarting application')

        # Not a deployment
        params['deployment'] = False

        environment = tagopsdb.Environment.get(env=params['env'])

        restart_targets = []

        if apptypes:
            for apptype in apptypes:
                pkg = self.get_package_for_target(apptype, environment)
                if pkg is None:
                    continue

                for host in apptype.hosts:
                    if host.environment == environment.environment:
                        restart_targets.append((host, pkg))

        elif hosts:
            for host in hosts:
                pkg = self.get_package_for_target(
                    host.target, environment
                )
                if pkg is None:
                    continue

                restart_targets.append((host, pkg))

        if not restart_targets:
            raise tds.exceptions.InvalidOperationError(
                'Nothing to restart for project "%s" in %s environment',
                package.name, environment.environment
            )

        restart_targets.sort(key=lambda x: (x[0].name, x[1].name))

        restart_results = {}

        delay = params.get('delay', None)
        for i, (host, pkg) in enumerate(restart_targets):
            # TODO: rework restart_hosts to take a list of hosts/pkgs
            restart_result = self.restart_host(host.name, pkg.name)
            restart_results[(host, pkg)] = restart_result[0]

            if delay is not None and (i+1) < len(restart_targets):
                log.log(5, 'Sleeping for %d seconds...', delay)
                time.sleep(delay)

        return dict(result=restart_results)

    @input_validate('package_hostonly')
    @input_validate('targets')
    @input_validate('application')
    def redeploy(self, application, package, hosts=None, apptypes=None,
                 **params):
        """Redeploy given application to requested tiers or hosts"""

        raise tds.exceptions.InvalidOperationError(
            'The "redeploy" subcommand has been replaced by "fix".  '
            'Please use "tds deploy fix" instead.'
        )

    @input_validate('package_hostonly')
    @input_validate('targets')
    @input_validate('application')
    def fix(self, application, package, hosts=None, apptypes=None,
            **params):
        """Fix failed deployments for a given application on requested tiers
           or hosts
        """

        log.debug('Fixing failed deployments for application')

        apptypes = self.get_app_info(
            package, hosts, apptypes, params, hostonly=True
        )
        app_dep_map = self.find_app_deployments(package, apptypes, params)

        if not len(list(filter(None, app_dep_map.itervalues()))):
            raise tds.exceptions.InvalidOperationError(
                'Nothing to fix for application %r in %s environment',
                application.name, self.envs[params['env']]
            )

        if package.app_deployments:
            deployment = package.app_deployments[-1].deployment
        else:
            deployment = package.host_deployments[-1].deployment
        params['package_name'] = package.name
        params['version'] = package.version

        self.send_notifications(
            hosts, apptypes, application=application, **params
        )
        self.perform_redeployments(
            hosts, apptypes, params, deployment, app_dep_map, package.id
        )

        tagopsdb.Session.commit()
        log.debug('Committed database changes')

        return dict()

    @input_validate('package')
    @input_validate('targets')
    @input_validate('application')
    def validate(self, application, package, hosts=None, apptypes=None,
                 **params):
        """Validate a given version of a given application"""

        log.debug('Validating for given application')

        # Not a deployment
        params['deployment'] = False

        apptypes = self.get_app_info(package, hosts, apptypes, params)
        app_dep_map = self.find_app_deployments(package, apptypes, params)

        if not len(list(filter(None, app_dep_map.itervalues()))):
            raise tds.exceptions.InvalidOperationError(
                'No deployments to validate for application "%s" '
                'in %s environment', application.name,
                self.envs[params['env']]
            )

        app_dep_map = self.determine_validations(
            params, apptypes, app_dep_map
        )
        self.perform_validations(params, app_dep_map)

        tagopsdb.Session.commit()
        log.debug('Committed database changes')

        return dict()
