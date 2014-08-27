'''
Controller for 'deploy' commands
'''
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
import tds.deploy_strategy

import logging

from .base import BaseController, validate

log = logging.getLogger('tds')


def create_deployment(project, **params):
    'Translate the common "params" argument into a Deployment instance'
    return tds.model.Deployment(
        actor=tds.model.Actor(
            name=params.get('user'),
            groups=params.get('groups'),
        ),
        action=dict(
            command=params.get('command_name'),
            subcommand=params.get('subcommand_name'),
        ),
        project=project,
        package=tds.model.Package(
            name=params.get('package_name'),
            version=params.get('version'),
        ),
        target=dict(
            environment=params.get('environment'),
            apptypes=params.get('apptypes'),
        ),
    )


class DeployController(BaseController):

    """Commands to manage deployments for supported applications"""

    dep_types = {'promote': 'Deployment',
                 'redeploy': 'Redeployment',
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
        'add_apptype': 'admin',
        'delete_apptype': 'admin',
        'invalidate': 'environment',
        'show': 'environment',
        'validate': 'environment',
        'promote': 'environment',
        'redeploy': 'environment',
        'rollback': 'environment',
        'restart': 'environment',
    }

    def __init__(self, config):
        """Basic initialization"""
        super(DeployController, self).__init__(config)
        self._deploy_strategy = tds.deploy_strategy.TDSMCODeployStrategy(
            **self.app_config['mco']
        )

    @property
    def deploy_strategy(self):
        '''
        Accessor for the DeployStrategy instance used by this object
        '''
        return self._deploy_strategy

    @tds.utils.debug
    def check_previous_environment(self, project, params, pkg_id, app_id):
        """Ensure deployment for previous environment for given package
           and apptier was validated; this is only relevant for staging
           and production environments
        """
        # Note: this will currently allow any user to force
        # a deployment without previous tier requirement;
        # the use of '--force' needs to be authorized further up

        if not self.requires_tier_progression or params['force']:
            log.debug(
                'Previous environment not required for %r or "--force" '
                'option in use',
                project.name
            )
            return True

        log.debug('Checking for validation in previous environment')

        if params['environment'] != 'dev':
            prev_env = self.get_previous_environment(params['environment'])
            log.log(5, 'Previous environment is: %s', prev_env)

            prev_deps = tagopsdb.deploy.deploy.find_app_deployment(
                pkg_id,
                [app_id],
                self.envs[prev_env]
            )
            # There might be no deployment available; otherwise
            # there should only be one deployment here
            if not prev_deps:
                raise Exception(
                    'Package "%s@%s" never validated in "%s" environment for '
                    'target "%s"',
                    project.name, params['version'],
                    prev_env, tds.model.DeployTarget.get(id=app_id).name
                )

            prev_app_dep, prev_app_type, prev_dep_type, \
                prev_pkg = prev_deps[0]
            log.log(5, 'Previous application deployment is: %r',
                    prev_app_dep)
            log.log(5, 'Previous application type is: %s',
                    prev_app_type)
            log.log(5, 'Previous deployment type is: %s',
                    prev_dep_type)
            log.log(5, 'Previous package is: %r', prev_pkg)

            if (prev_dep_type != 'deploy' or
                    prev_app_dep.status != 'validated'):
                log.info(
                    'Application %r with version %r not fully '
                    'deployed or validated to previous environment '
                    '(%s) for apptype %r', project.name,
                    params['version'], prev_env, prev_app_type
                )
                return False

        log.log(5, 'In development environment, nothing to check')

        return True

    @tds.utils.debug
    def check_for_current_deployment(self, params, app_id, hosts=None):
        """For the current app type, see if there are any current deployments
           running and notify if there is
        """

        log.debug(
            'Checking for a deployment of the same application '
            'already in progress'
        )

        time_delta = timedelta(hours=1)  # Harcoded to an hour for now
        log.log(5, 'time_delta is: %s', time_delta)

        dep_info = tagopsdb.deploy.deploy.find_running_deployment(
            app_id,
            self.envs[params['environment']],
            hosts=hosts
        )

        if dep_info:
            log.debug('Current deployment found')

            dep_type, data = dep_info
            log.log(5, 'Deployment type is: %s', dep_type)

            if dep_type == 'tier':
                dep_user, dep_realized, dep_env, dep_apptype = data
                log.log(5, 'Deployment user is: %s', dep_user)
                log.log(5, 'Deployment realized is: %s', dep_realized)
                log.log(5, 'Deployment environment is: %s', dep_env)
                log.log(5, 'Deployment apptype is: %s', dep_apptype)

                if datetime.now() - dep_realized < time_delta:
                    log.info(
                        'User "%s" is currently running a '
                        'deployment for the %s app tier in the %s '
                        'environment, skipping...',
                        dep_user, dep_apptype, dep_env
                    )
                    return True
            else:   # dep_type is 'host'
                dep_hosts = []

                for entry in data:
                    dep_user, dep_realized, dep_hostname, dep_env = entry
                    log.log(5, 'Deployment user is: %s', dep_user)
                    log.log(5, 'Deployment realized is: %s', dep_realized)
                    log.log(5, 'Deployment hostname is: %s', dep_hostname)
                    log.log(5, 'Deployment environment is: %s', dep_env)

                    if datetime.now() - dep_realized < time_delta:
                        log.log(
                            5, 'Host %r active with deployment',
                            dep_hostname
                        )
                        dep_hosts.append(dep_hostname)

                if dep_hosts:
                    # Allow separate hosts to get simultaneous deployments
                    if (hosts is None or
                            not set(dep_hosts).isdisjoint(set(hosts))):
                        host_list = ', '.join(dep_hosts)
                        log.info(
                            'User "%s" is currently running a '
                            'deployment for the hosts "%s" in '
                            'the %s environment, skipping...',
                            dep_user, host_list, dep_env
                        )
                        return True

        log.debug('No current deployment found')
        return False

    @tds.utils.debug
    def check_tier_state(self, project, params, pkg_id, app_dep):
        """Ensure state of tier (from given app deployment) is consistent
           with state and deployment package versions
        """

        log.debug('Checking state of tier')

        apptype_hosts = tagopsdb.deploy.deploy.find_hosts_for_app(
            app_dep.app_id,
            self.envs[params['environment']]
        )
        apptype_hostnames = [x.hostname for x in apptype_hosts]
        log.log(5, 'Tier hosts are: %s', ', '.join(apptype_hostnames))

        dep_hosts = \
            tagopsdb.deploy.deploy.find_host_deployments_by_package_name(
                project.name,
                apptype_hostnames
            )
        dep_hostnames = [x.hostname for x in dep_hosts]

        if dep_hostnames:
            log.log(5, 'Deployed hosts are: %s', ', '.join(dep_hostnames))

        missing_deps = list(set(apptype_hostnames) - set(dep_hostnames))
        version_diffs = [x.hostname for x in dep_hosts
                         if int(x.version) != params['version']]

        if version_diffs:
            log.log(5, 'Version differences on: %s', ', '.join(version_diffs))

        not_ok_hosts = tagopsdb.deploy.deploy.find_host_deployments_not_ok(
            pkg_id,
            app_dep.app_id,
            self.envs[params['environment']]
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
        """Deploy specified package to a given host"""

        return self.deploy_strategy.deploy_to_host(
            dep_host,
            app,
            version,
            retry
        )

    @tds.utils.debug
    def restart_host(self, dep_host, app, retry=4):
        'Restart a host'
        return self.deploy_strategy.restart_host(dep_host, app, retry)

    @tds.utils.debug
    def deploy_to_hosts(self, project, params, dep_hosts, dep_id, redeploy=False):
        """Perform deployment on given set of hosts (only doing those
           that previously failed with a redeploy)
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

        for dep_host in sorted(dep_hosts, key=lambda host: host.hostname):
            pkg = tagopsdb.deploy.deploy.find_app_by_depid(dep_id)
            app, version = pkg.pkg_name, pkg.version
            log.log(5, 'Project name and version: %s %s', app, version)

            host_dep = tagopsdb.deploy.deploy.find_host_deployment_by_depid(
                dep_id,
                dep_host.hostname
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
                    project.name
                )
                host_dep = tagopsdb.deploy.deploy.add_host_deployment(
                    dep_id,
                    dep_host.id,
                    params['user'],
                    'inprogress'
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
    def deploy_to_hosts_or_tiers(self, project, params, dep_id, app_host_map,
                                 app_dep_map, redeploy=False):
        """Do the deployment to the requested hosts or application tiers"""

        log.debug('Deploying to requested hosts or application tiers')

        app_ids = []

        if params.get('hosts', None):
            log.log(5, 'Deployment is for hosts...')

            for app_id, hosts in app_host_map.iteritems():
                if self.check_for_current_deployment(params, app_id,
                                                     hosts=hosts):
                    log.log(
                        5, 'App ID %s already has deployment, skipping...',
                        app_id
                    )
                    continue

                app_ids.append(app_id)

                log.log(
                    5, 'Hosts being deployed to are: %s', ', '.join(hosts)
                )
                dep_hosts = [
                    tagopsdb.deploy.deploy.find_host_by_hostname(x)
                    for x in hosts
                ]

                # We want the tier status updated only if doing
                # a rollback
                if self.deploy_to_hosts(project, params, dep_hosts, dep_id,
                                        redeploy=redeploy) \
                        and params['subcommand_name'] == 'rollback':
                    app_dep = app_dep_map[app_id][0]
                    app_dep.status = 'complete'
        else:
            log.log(5, 'Deployment is for application tiers...')

            for app_id, dep_info in app_dep_map.iteritems():
                if self.check_for_current_deployment(params, app_id):
                    log.log(
                        5, 'App ID %s already has deployment, skipping...',
                        app_id
                    )
                    continue

                app_ids.append(app_id)

                if redeploy:
                    app_dep, app_type, _dep_type, pkg = dep_info

                    # Don't redeploy to a validated tier
                    if app_dep.status == 'validated':
                        log.info(
                            'Application "%s" with version "%s" '
                            'already validated on app type %s"',
                            project.name, pkg.version,
                            app_type
                        )
                        continue
                else:
                    app_dep = tagopsdb.deploy.deploy.add_app_deployment(
                        dep_id,
                        app_id,
                        params['user'],
                        'inprogress',
                        self.envs[params['environment']]
                    )

                try:
                    dep_hosts = tagopsdb.deploy.deploy.find_hosts_for_app(
                        app_id,
                        self.envs[params['environment']]
                    )
                except tagopsdb.exceptions.DeployException:
                    app_type = dep_info[1]
                    log.info(
                        'No hosts available for application type '
                        '"%s" in %s environment',
                        app_type, self.envs[params['environment']]
                    )

                    # Set the deployment status due to no hosts
                    # being available
                    app_dep.status = 'incomplete'
                    log.log(
                        5, 'Setting deployment status to: %s', app_dep.status
                    )
                    continue

                if self.deploy_to_hosts(project, params, dep_hosts, dep_id,
                                        redeploy=redeploy):
                    app_dep.status = 'complete'
                else:
                    app_dep.status = 'incomplete'

                log.log(5, 'Setting deployment status to: %s', app_dep.status)

        if params['environment'] == 'prod':
            log.info(
                'Please review the following Nagios group views '
                'or the deploy health status:'
            )

            for app_id in app_ids:
                app_type = tagopsdb.deploy.deploy.find_apptype_by_appid(app_id)
                log.info(
                    '  https://nagios.tagged.com/nagios/cgi-bin/'
                    'status.cgi?style=detail&hostgroup=app.%s', app_type
                )

    @tds.utils.debug
    def determine_invalidations(self, project, params, app_ids, app_dep_map):
        """Determine which application tiers need invalidations performed"""

        log.debug(
            'Determining invalidations for requested application types'
        )

        curr_deps = tagopsdb.deploy.deploy.find_latest_deployed_version(
            project.name,
            self.envs[params['environment']],
            apptier=True
        )
        curr_dep_versions = {}

        for app_type, version, revision in curr_deps:
            log.log(
                5, 'App type: %s, Version: %s, Revision %s',
                app_type, version, revision
            )
            curr_dep_versions[app_type] = int(version)

        for app_id in app_ids:
            if not app_dep_map[app_id]:
                log.log(
                    5, 'Application ID %r is not in deployment/'
                    'application map', app_id
                )
                continue

            valid = True

            app_dep, app_type, dep_type, pkg = app_dep_map[app_id]
            log.log(5, 'Application deployment is: %r', app_dep)
            log.log(5, 'Application type is: %s', app_type)
            log.log(5, 'Deployment type is: %s', dep_type)
            log.log(5, 'Package is: %r', pkg)

            # Ensure version to invalidate isn't the current
            # deployment for this app type
            if curr_dep_versions.get(app_type, None) == params['version']:
                log.info(
                    'Unable to invalidate application "%s" with '
                    'version "%s" for apptype "%s" as that version '
                    'is currently deployed for the apptype',
                    project.name, params['version'], app_type
                )
                valid = False

            if valid:
                if app_dep.status != 'validated':
                    raise Exception(
                        'Package "%s@%s" currently deployed on target "%s"',
                        pkg.name, pkg.version, app_type
                    )

            if not valid:
                log.log(
                    5, 'Deleting application ID %r from '
                    'deployment/application map', app_id
                )
                del app_dep_map[app_id]

        log.log(5, 'Deployment/application map is: %r', app_dep_map)

        return app_dep_map

    @tds.utils.debug
    def determine_new_deployments(self, project, params, pkg_id, app_ids, app_host_map,
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
        for app_id in app_ids:
            valid = self.check_previous_environment(project, params, pkg_id, app_id)

            if valid:
                if not app_dep_map[app_id]:
                    log.log(
                        5, 'Application ID %r is not in '
                        'deployment/application map', app_id
                    )
                    continue

                app_dep, app_type, dep_type, pkg = app_dep_map[app_id]
                log.log(5, 'Application deployment is: %r', app_dep)
                log.log(5, 'Application type is: %s', app_type)
                log.log(5, 'Deployment type is: %s', dep_type)
                log.log(5, 'Package is: %r', pkg)

                if (app_dep.status != 'invalidated' and dep_type == 'deploy'
                        and pkg.version == params['version']):
                    log.info(
                        'Application %r with version "%s" '
                        'already deployed to this environment (%s) '
                        'for apptype %r',
                        project.name, params['version'],
                        self.envs[params['environment']], app_type
                    )
                    valid = False

            if not valid:
                if params.get('hosts', None):
                    log.log(
                        5, 'Deleting application ID %r from '
                        'host/application map', app_id
                    )
                    del app_host_map[app_id]
                else:
                    log.log(
                        5, 'Deleting application ID %r from '
                        'deployment/application map', app_id
                    )
                    del app_dep_map[app_id]

        log.log(5, 'Host/application map is: %r', app_host_map)
        log.log(5, 'Deployment/application map is: %r', app_dep_map)

        return (app_host_map, app_dep_map)

    @staticmethod
    def determine_redeployments(pkg_id):
        """Determine which application tiers or hosts need redeployments"""

        log.debug(
            'Determining redeployments for requested application '
            'types or hosts'
        )

        pkg_deps = tagopsdb.deploy.deploy.find_deployment_by_pkgid(pkg_id)
        last_pkg_dep = pkg_deps[0]  # Guaranteed to have at least one

        return last_pkg_dep.id

    @staticmethod
    def determine_restarts(pkg_id):
        """Determine which application tiers or hosts need restarts"""

        log.debug(
            'Determining restarts for requested application '
            'types or hosts'
        )

        pkg_deps = tagopsdb.deploy.deploy.find_deployment_by_pkgid(pkg_id)
        last_pkg_dep = pkg_deps[0]  # Guaranteed to have at least one

        return last_pkg_dep.id

    @tds.utils.debug
    def determine_rollbacks(self, params, app_ids, app_host_map, app_dep_map):
        """Determine which application tiers or hosts need rollbacks"""

        log.debug('Determining rollbacks for requested application types')

        app_pkg_map = {}

        for app_id in app_ids:
            if app_dep_map.get(app_id, None) is None:
                log.log(
                    5, 'Application ID %r is not in '
                    'deployment/application map', app_id
                )
                continue

            valid = True

            _app_dep, app_name, _dep_type, package = app_dep_map[app_id]

            pkg_def = package.package_definition

            if params.get('hosts', None):
                prev_dep_info = \
                    tagopsdb.deploy.deploy.find_latest_validated_deployment(
                        pkg_def.name, app_id,
                        self.envs[params['environment']])
            else:
                prev_dep_info = \
                    tagopsdb.deploy.deploy.find_previous_validated_deployment(
                        pkg_def.name, app_id,
                        self.envs[params['environment']])

            if prev_dep_info is None:
                log.info(
                    'No previous deployment to roll back to for '
                    'application "%s" for app type "%s" in %s '
                    'environment', pkg_def.name, app_name,
                    self.envs[params['environment']]
                )
                valid = False
            else:
                prev_app_dep, prev_pkg_id = prev_dep_info
                log.log(
                    5, 'Previous application deployment is: %r',
                    prev_app_dep
                )
                log.log(5, 'Previous package ID is: %s', prev_pkg_id)

                app_pkg_map[app_id] = prev_pkg_id

            if not valid:
                log.log(
                    5, 'Deleting application ID %r from '
                    'deployment/application map', app_id
                )
                del app_dep_map[app_id]

        log.log(5, 'Package/application map is: %r', app_pkg_map)
        log.log(5, 'Host/application map is: %r', app_host_map)
        log.log(5, 'Deployment/application map is: %r', app_dep_map)

        return (app_pkg_map, app_host_map, app_dep_map)

    @tds.utils.debug
    def determine_validations(self, project, params, pkg_id, app_ids, app_dep_map):
        """Determine which application tiers need validation performed"""

        for app_id in app_ids:
            if not app_dep_map[app_id]:
                log.log(
                    5, 'Application ID %r is not in '
                    'deployment/application map', app_id
                )
                continue

            valid = True

            app_dep, app_type, dep_type, pkg = app_dep_map[app_id]
            log.log(5, 'Application deployment is: %r', app_dep)
            log.log(5, 'Application type is: %s', app_type)
            log.log(5, 'Deployment type is: %s', dep_type)
            log.log(5, 'Package is: %r', pkg)

            if app_dep.status == 'validated':
                log.info(
                    'Deployment for application %r for apptype %r '
                    'already validated in %s environment',
                    project.name, app_type,
                    self.envs[params['environment']]
                )
                valid = False

            if valid:
                # Ensure tier state is consistent
                result, missing, diffs, not_ok_hostnames = \
                    self.check_tier_state(project, params, pkg_id, app_dep)

                if result != 'ok':
                    log.info(
                        'Encountered issues while validating '
                        'version %r of application %r:',
                        params['version'], project.name
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
                    'deployment/application map', app_id
                )
                del app_dep_map[app_id]

        log.log(5, 'Deployment/application map is: %r', app_dep_map)

        return app_dep_map

    @tds.utils.debug
    def ensure_explicit_destinations(self, project, params):
        """Make sure multiple application types are explicit"""

        log.debug(
            'Ensuring multiple application types are explicitly mentioned'
        )

        if not params['explicit'] and len(self.get_app_types(project, params)) > 1:
            log.info(
                'Application "%s" has multiple corresponding '
                'app types, please use "--apptypes" or '
                '"--all-apptypes"', project.name
            )
            raise SystemExit(1)

    @tds.utils.debug
    def ensure_newer_versions(self, project, params):
        """Ensure version being deployed is more recent than
           the currently deployed versions on requested app types
        """

        log.debug(
            'Ensuring version to deploy is newer than the '
            'currently deployed version'
        )

        newer_versions = []
        dep_versions = tagopsdb.deploy.deploy.find_latest_deployed_version(
            project.name,
            self.envs[params['environment']],
            apptier=True
        )

        for dep_app_type, dep_version, dep_revision in dep_versions:
            if params['apptypes'] and dep_app_type not in params['apptypes']:
                continue

            log.log(
                5, 'Deployment application type is: %s',
                dep_app_type
            )
            log.log(5, 'Deployment version is: %s', dep_version)
            log.log(5, 'Deployment revision is: %s', dep_revision)

            # Currently not using revision (always '1' at the moment)
            # 'dep_version' must be typecast to an integer as well,
            # since the DB stores it as a string - may move away from
            # integers for versions in the future, so take note here
            if params['version'] < int(dep_version):
                log.log(
                    5, 'Deployment version %r is newer than '
                    'requested version %r', dep_version,
                    params['version']
                )
                newer_versions.append(dep_app_type)

        if newer_versions:
            app_type_list = ', '.join(['"%s"' % x for x in newer_versions])
            log.info(
                'Application %r for app types %s have newer '
                'versions deployed than the requested version %r',
                project.name, app_type_list, params['version']
            )
            return False

        return True

    @tds.utils.debug
    def find_app_deployments(self, pkg_id, app_ids, params):
        """Find all relevant application deployments for the requested
        app types and create an application/deployment mapping,
        keeping track of which app types have a current deployment
        and which don't
        """

        log.debug('Finding all relevant application deployments')

        package = tagopsdb.Package.get(id=pkg_id)
        environment = tagopsdb.Environment.get(
            environment=self.envs[params['environment']]
        )

        app_deployments = {}

        for app_id in app_ids:
            app = tagopsdb.Application.get(id=app_id)
            if app is None:
                app_deployments[app_id] = None
                continue

            for app_dep in reversed(app.app_deployments):
                if app_dep.environment_obj != environment:
                    continue
                if app_dep.deployment.package != package:
                    continue

                app_deployments[app_id] = (
                    app_dep, app.name, app_dep.deployment.type, package
                )
                break
            else:
                app_deployments[app_id] = None

        return app_deployments

    @tds.utils.debug
    def get_app_info(self, project, params, hostonly=False):
        """Verify requested package and which hosts or app tiers
        to install the package; for hosts a mapping is kept between
        them and their related app types
        """

        log.debug(
            'Verifying requested package is correct for given '
            'application tiers or hosts'
        )

        if params.get('hosts', None):
            log.log(5, 'Verification is for hosts...')

            no_exist_hosts = []
            for hostname in params['hosts']:
                if tagopsdb.Host.get(name=hostname) is None:
                    no_exist_hosts.append(hostname)

            if no_exist_hosts:
                raise Exception(
                    "These hosts do not exist: %s", ', '.join(no_exist_hosts)
                )

            try:
                pkg_id, app_host_map = self.verify_package(project, params,
                                                           hostonly=hostonly)
            except ValueError, e:
                log.error('%s for given project and hosts', e)
                raise SystemExit(1)

            host_deps = \
                tagopsdb.deploy.deploy.find_host_deployments_by_package_name(
                    project.name,
                    params['hosts']
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
                        'Project %r with version %r already '
                        'deployed to host %r', project.name,
                        curr_version, hostname
                    )
                    app_host_map[app_id].remove(hostname)

                    if not app_host_map[app_id]:
                        log.log(
                            5, 'Application ID %r is not in '
                            'host/application map', app_id
                        )
                        del app_host_map[app_id]

            app_ids = app_host_map.keys()
        else:
            log.log(5, 'Verification is for application tiers...')

            try:
                pkg_id, app_ids = self.verify_package(project, params)
            except ValueError, e:
                log.error('%s for given project and application tiers', e)
                raise SystemExit(1)

            app_host_map = None   # No need for this for tiers

        log.log(5, 'Package ID is: %s', pkg_id)
        log.log(
            5, 'Application IDs are: %s',
            ', '.join([str(x) for x in app_ids])
        )
        log.log(5, 'Host/application map is: %r', app_host_map)

        return (pkg_id, app_ids, app_host_map)

    def get_app_types(self, project, params):
        """Determine application IDs for deployment"""

        log.debug('Determining the application IDs for deployment')

        try:
            app_packages = project.targets
        except tagopsdb.exceptions.RepoException as e:
            log.error(e)
            raise SystemExit(1)

        if params.get('apptypes', None):
            try:
                app_defs = [
                    tagopsdb.deploy.deploy.find_app_by_apptype(x)
                    for x in params['apptypes']
                ]
                log.log(
                    5, 'Definitions for applications types are: '
                    '%s', ', '.join([repr(x) for x in app_defs])
                )
            except tagopsdb.exceptions.DeployException as e:
                log.error(e)
                raise SystemExit(1)

            new_ids = set(getattr(x, 'id', None) for x in app_defs)
            all_ids = set(x.id for x in app_packages)

            if new_ids.issubset(all_ids) and None not in new_ids:
                app_packages = app_defs
            else:
                raise Exception(
                    'Valid apptypes for project "%s" are: %s',
                    project.name, [str(x.name) for x in app_packages]
                )

        app_ids = [x.id for x in app_packages]
        log.log(
            5, 'Final application IDs are: %s',
            ', '.join([str(x) for x in app_ids])
        )

        return app_ids

    @tds.utils.debug
    def get_package(self, project, params, app_ids, hostonly=False):
        """Get the package ID for the current project and version
           (or most recent deployed version if none is given) for
           a given set of application types
        """

        log.debug('Determining package ID for given project')

        app_types = map(tagopsdb.deploy.deploy.find_apptype_by_appid, app_ids)
        log.log(5, 'Application types are: %s', ', '.join(app_types))

        if 'version' in params:
            log.log(5, 'Using given version %r for package', params['version'])
            version = params['version']
        else:
            log.log(5, 'Determining version for package')

            # Must determine latest deployed version(s);
            # they must all use the same package version
            # (Tuple of app_type, version, revision returned
            #  with DB query)
            apptier = not hostonly

            package_defs = [
                x.package_definition
                for app_id in app_ids
                for x in tagopsdb.ProjectPackage.find(
                    project_id=project.id, app_id=app_id
                )
            ]

            assert len(package_defs) == len(app_ids)

            last_deps = sum([
                tagopsdb.deploy.deploy.find_latest_deployed_version(
                    pkg_def.name,
                    self.envs[params['environment']],
                    apptier=apptier
                ) for pkg_def in package_defs],
                []
            )

            log.log(5, 'Latest validated deployments: %r', last_deps)

            if hostonly:
                versions = [x.version for x in last_deps
                            if x.app_id in app_ids]
            else:
                versions = [x.version for x in last_deps
                            if x.appType in app_types]

            log.log(5, 'Found versions are: %s', ', '.join(versions))

            if not versions:
                log.info(
                    'Project "%s" has no current tier/host '
                    'deployments to verify for the given apptypes/'
                    'hosts', project.name
                )
                raise SystemExit(1)

            if not all(x == versions[0] for x in versions):
                raise ValueError('Multiple versions not allowed')

            version = versions[0]
            log.log(5, 'Determined version is: %s', version)
            params['current_version'] = version   # Used for notifications

        pkg = None
        try:
            # Revision hardcoded to '1' for now
            pkg = tagopsdb.deploy.package.find_package(
                project.name,
                version,
                '1'
            )
        except tagopsdb.exceptions.PackageException as e:
            log.error(e)
            raise SystemExit(1)

        return pkg

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
    def perform_deployments(self, project, params, pkg_id, app_host_map, app_dep_map):
        """Perform all deployments to the requested application tiers or
           hosts
        """

        log.debug('Performing deployments to application tiers or hosts')

        # All is well, now do the deployment
        #   1. See if a deployment entry already exists in DB and use it,
        #      otherwise create a new one
        #   2. If deploying to tier, add an app deployment entry in DB
        #   3. Determine the appropriate hosts to deploy the application
        #   4. Do the deploy to the hosts
        dep_id = None
        pkg_deps = tagopsdb.deploy.deploy.find_deployment_by_pkgid(pkg_id)

        if pkg_deps:
            log.log(5, 'Found existing deployment')

            last_pkg_dep = pkg_deps[0]
            log.log(5, 'Package deployment is: %r', last_pkg_dep)

            if last_pkg_dep.dep_type == 'deploy':
                dep_id = last_pkg_dep.id
                log.log(5, 'Deployment ID is: %s', dep_id)

        if dep_id is None:
            log.log(5, 'Creating new deployment')

            pkg_dep = tagopsdb.deploy.deploy.add_deployment(
                pkg_id,
                params['user'],
                'deploy'
            )
            dep_id = pkg_dep.id
            log.log(5, 'Deployment ID is: %s', dep_id)

        self.deploy_to_hosts_or_tiers(project, params, dep_id, app_host_map,
                                      app_dep_map)

    @staticmethod
    def perform_invalidations(app_dep_map):
        """Perform all invalidations to the requested application tiers"""

        log.debug('Performing invalidations to application tiers')

        for dep_info in app_dep_map.itervalues():
            app_dep, app_type, dep_type, pkg = dep_info
            log.log(5, 'Application deployment is: %r', app_dep)
            log.log(5, 'Application type is: %s', app_type)
            log.log(5, 'Deployment type is: %s', dep_type)
            log.log(5, 'Package is: %r', pkg)

            app_dep.status = 'invalidated'

    @tds.utils.debug
    def perform_redeployments(self, project, params, dep_id, app_host_map,
                              app_dep_map):
        """Perform all redeployments to the requested application tiers or
           hosts
        """

        log.debug('Performing redeployments to application tiers or hosts')

        self.deploy_to_hosts_or_tiers(project, params, dep_id, app_host_map,
                                      app_dep_map, redeploy=True)

    @tds.utils.debug
    def perform_restarts(self, params, dep_id, app_host_map, app_dep_map):
        """Perform all restarts to the requested application tiers or hosts"""

        log.debug('Performing restart to application tiers or hosts')

        self.restart_hosts_or_tiers(params, dep_id, app_host_map, app_dep_map)

    @tds.utils.debug
    def perform_rollbacks(self, project, params, app_pkg_map, app_host_map,
                          app_dep_map):
        """Perform all rollbacks to the requested application tiers
           or hosts
        """

        log.debug('Performing rollbacks to application tiers or hosts')

        # Since a roll back could end up at different versions for
        # each application tier, must do each tier (or host(s) in
        # tier) on its own
        for app_id, pkg_id in app_pkg_map.iteritems():
            app_dep, app_type, dep_type, pkg = app_dep_map[app_id]
            log.log(5, 'Application deployment is: %r', app_dep)
            log.log(5, 'Application type is: %s', app_type)
            log.log(5, 'Deployment type is: %s', dep_type)
            log.log(5, 'Package is: %r', pkg)

            app_id = app_dep.app_id
            log.log(5, 'Application ID is: %s', app_id)

            if app_host_map is None or not app_host_map.get(app_id, None):
                log.log(5, 'Creating new deployment')

                pkg_dep = tagopsdb.deploy.deploy.add_deployment(
                    pkg_id,
                    params['user'],
                    'deploy'
                )
                dep_id = pkg_dep.id
                log.log(5, 'Deployment ID is: %s', dep_id)
            else:
                # Reset app deployment to 'inprogress' (if tier rollback)
                # or 'incomplete' (if host rollback), will require
                # revalidation
                if params.get('hosts', None):
                    app_dep.status = 'incomplete'
                else:
                    app_dep.status = 'inprogress'

                tagopsdb.Session.commit()

                dep_id = app_dep.deployment_id

            if app_host_map is None:
                single_app_host_map = None
            else:
                single_app_host_map = {app_id: app_host_map[app_id]}

            single_app_dep_map = {app_id: app_dep_map[app_id]}

            self.deploy_to_hosts_or_tiers(project, params, dep_id, single_app_host_map,
                                          single_app_dep_map)

    @tds.utils.debug
    def perform_validations(self, project, params, app_dep_map):
        """Perform all validations to the requested application tiers"""

        log.debug('Performing validations to application tiers')

        for dep_info in app_dep_map.itervalues():
            app_dep, app_type, dep_type, pkg = dep_info
            log.log(5, 'Application deployment is: %r', app_dep)
            log.log(5, 'Application type is: %s', app_type)
            log.log(5, 'Deployment type is: %s', dep_type)
            log.log(5, 'Package is: %r', pkg)

            # Commit to DB immediately
            app_dep.status = 'validated'
            tagopsdb.Session.commit()

            log.log(5, 'Committed database (nested) change')
            log.log(5, 'Clearing host deployments for application tier')
            tagopsdb.deploy.deploy.delete_host_deployments(
                project.name,
                app_dep.app_id,
                self.envs[params['environment']]
            )

    @tds.utils.debug
    def restart_hosts(self, params, dep_hosts, dep_id):
        """Restart application on a given set of hosts"""

        log.debug('Restarting application on given hosts')

        failed_hosts = []

        for dep_host in sorted(dep_hosts, key=lambda host: host.hostname):
            log.log(5, 'Hostname is: %s', dep_host.hostname)

            pkg = tagopsdb.deploy.deploy.find_app_by_depid(dep_id)
            app = pkg.pkg_name
            log.log(5, 'Application is: %s', app)

            success, info = self.restart_host(dep_host.hostname, app)

            if not success:
                log.log(
                    5, 'Failed to restart application on host %r',
                    dep_host.hostname
                )
                failed_hosts.append((dep_host.hostname, info))


            delay = params.get('delay', None)
            if delay is not None:
                log.log(5, 'Sleeping for %d seconds...', delay)
                time.sleep(delay)

        # If any hosts failed, show failure information for each
        if failed_hosts:
            log.info('Some hosts had failures:\n')

            for failed_host, reason in failed_hosts:
                log.info('-----')
                log.info('Hostname: %s', failed_host)
                log.info('Reason: %s', reason)

    @tds.utils.debug
    def restart_hosts_or_tiers(self, params, dep_id, app_host_map,
                               app_dep_map):
        """Restart the application on the requested hosts or application
           tiers
        """

        log.debug(
            'Restarting application on requested application '
            'tiers or hosts'
        )

        if params.get('hosts', None):
            log.log(5, 'Restarts are for hosts...')

            hostnames = []

            for hosts in app_host_map.itervalues():
                hostnames.extend(hosts)

            log.log(5, 'Hostnames are: %s', ', '.join(hostnames))

            dep_hosts = map(
                tagopsdb.deploy.deploy.find_host_by_hostname,
                hostnames
            )
            self.restart_hosts(params, dep_hosts, dep_id)
        else:
            log.log(5, 'Restarts are for application tiers...')

            for app_id in app_dep_map.iterkeys():
                log.log(5, 'Application ID is: %s', app_id)

                dep_hosts = tagopsdb.deploy.deploy.find_hosts_for_app(
                    app_id,
                    self.envs[params['environment']]
                )
                self.restart_hosts(params, dep_hosts, dep_id)

    @tds.utils.debug
    def send_notifications(self, project, params):
        """Send notifications for a given deployment"""

        log.debug('Sending notifications for given deployment')

        deployment = create_deployment(project=project, **params)
        notification = tds.notifications.Notifications(self.app_config)
        notification.notify(deployment)

    @staticmethod
    def show_app_deployments(project, app_versions, env):
        """Show information for current deployment for a given application
           tier (or tiers)
        """

        log.debug(
            'Showing information for current deployments '
            'for application tiers'
        )

        if not app_versions:
            log.info(
                'No deployments to tiers for this application '
                '(for possible given version) yet'
            )
            log.info('in %s environment\n', env)
            return

        for app_type, version, revision in app_versions:
            log.info(
                'Deployment of %s to %s tier in %s environment:',
                project, app_type, env
            )
            log.info('==========\n')

            app_dep = tagopsdb.deploy.deploy.list_app_deployment_info(
                project,
                env,
                app_type,
                version,
                revision
            )

            dep, app_dep, pkg = app_dep

            log.info('Version: %s-%s', pkg.version, pkg.revision)
            log.info('Declared: %s', dep.declared)
            log.info('Declaring user: %s', dep.user)
            log.info('Realized: %s', app_dep.realized)
            log.info('Realizing user: %s', app_dep.user)
            log.info('App type: %s', app_type)
            log.info('Environment: %s', app_dep.environment)
            log.info('Deploy state: %s', dep.dep_type)
            log.info('Install state: %s', app_dep.status)
            log.info('')

    @staticmethod
    def show_host_deployments(project, version, revision, apptypes, env):
        """Show information for current deployment for a given host
           (or hosts)
        """

        log.debug(
            'Showing information for current deployments for hosts'
        )

        host_deps = tagopsdb.deploy.deploy.list_host_deployment_info(
            project,
            env,
            version=version,
            revision=revision,
            apptypes=apptypes
        )

        if not host_deps:
            log.info(
                'No deployments to hosts for this application '
                '(for possible given version)'
            )
            log.info('in %s environment\n', env)
        else:
            log.info(
                'Deployments of %s to hosts in %s environment:', project, env
            )
            log.info('==========\n')

            for dep, host_dep, hostname, pkg in host_deps:
                log.info('Version: %s-%s', pkg.version, pkg.revision)
                log.info('Declared: %s', dep.declared)
                log.info('Declaring user: %s', dep.user)
                log.info('Realized: %s', host_dep.realized)
                log.info('Realizing user: %s', host_dep.user)
                log.info('Hostname: %s', hostname)
                log.info('Deploy state: %s', dep.dep_type)
                log.info('Install state: %s', host_dep.status)
                log.info('')

    @staticmethod
    def verify_hosts(hosts, app_ids, environment):
        """Verify given hosts are in the correct environment and of the
           correct app IDs
        """

        log.debug(
            'Verifying hosts are in the correct environment '
            'and of a correct application type'
        )

        valid_hostnames = {}
        app_id_hosts_mapping = {}

        for app_id in app_ids:
            log.log(5, 'Application ID is: %s', app_id)

            try:
                hosts_for_app = tagopsdb.deploy.deploy.find_hosts_for_app(
                    app_id,
                    environment
                )
                hostnames = [x.hostname for x in hosts_for_app]
                log.log(
                    5, 'Hostnames for application ID are: %s',
                    ', '.join(hostnames)
                )

                valid_hostnames[app_id] = hostnames
            except tagopsdb.exceptions.DeployException as e:
                # Currently we should NOT fail on this; it will
                # be caught when checking the hosts involved
                log.warning(e)

        bad_hosts = []

        for hostname in hosts:
            log.log(5, 'Hostname is: %s', hostname)

            for app_id in valid_hostnames.iterkeys():
                log.log(
                    5, 'Application ID for hostname is: %s', app_id
                )

                if hostname in valid_hostnames[app_id]:
                    log.log(5, 'Hostname %r is valid', hostname)
                    host_map_list = \
                        app_id_hosts_mapping.setdefault(app_id, [])
                    host_map_list.append(hostname)
                    break
            else:
                log.log(5, 'Hostname %r was invalid', hostname)
                bad_hosts.append(hostname)

        if bad_hosts:
            log.info(
                'The following hosts are in the wrong environment '
                'or do not belong to a matching app type: %s',
                ', '.join(bad_hosts)
            )
            raise SystemExit(1)

        log.log(5, 'App ID/hosts map is: %r', app_id_hosts_mapping)

        return app_id_hosts_mapping

    @tds.utils.debug
    def verify_package(self, project, params, hostonly=False):
        """Ensure requested package is valid (exists in the software
           repository)
        """

        log.debug('Verifying requested package')

        app_ids = self.get_app_types(project, params)
        pkg = self.get_package(project, params, app_ids, hostonly)

        if pkg is None:
            return (pkg, app_ids)

        if params.get('hosts', None):
            log.log(5, 'Verification is for hosts...')

            app_host_map = self.verify_hosts(params['hosts'], app_ids,
                                             self.envs[params['environment']])
            log.log(5, 'Application/host map is: %r', app_host_map)

            return (pkg.id, app_host_map)
        else:
            log.log(5, 'Verification is for application tiers...')
            log.log(
                5,
                'Applications IDs are: %s',
                ', '.join([str(x) for x in app_ids])
            )

            return (pkg.id, app_ids)

    @validate('project')
    def add_apptype(self, project, **params):
        """Add a specific application type to the given project"""

        log.debug('Adding application type for project')

        try:
            package_location = tagopsdb.deploy.repo.find_app_location(
                project.name
            )
        except tagopsdb.exceptions.RepoException:
            raise Exception(
                "RepoException when finding package location for project: %s", project.name
            )

        try:
            pkg_def = tagopsdb.deploy.package.find_package_definition(
                project.id
            )
        except tagopsdb.exceptions.RepoException:
            raise Exception(
                # XXX: who cares?
                "No packages associated with project: %s", project.name
            )

        try:
            tagopsdb.deploy.repo.add_app_packages_mapping(
                package_location,
                project.delegate,
                pkg_def,
                [params['apptype']]
            )
        except tagopsdb.exceptions.RepoException:
            raise Exception(
                "Deploy target does not exist: %s", params['apptype']
            )

        tagopsdb.Session.commit()
        log.debug('Committed database changes')

        return dict(
            result=dict(
                target=params['apptype'],
                project=project.name
            )
        )

    @validate('project')
    def delete_apptype(self, project, **params):
        """Delete a specific application type from the given project"""

        log.debug('Removing application type for project')

        app = tagopsdb.deploy.repo.find_app_location(project.name)

        if app is None:
            raise Exception(
                'No app found for project "%s"', project.name
            )

        try:
            tagopsdb.deploy.repo.delete_app_packages_mapping(
                app,
                [params['apptype']]
            )
        except tagopsdb.exceptions.RepoException:
            raise Exception(
                'Target "%s" does not exist', params['apptype']
            )

        tagopsdb.Session.commit()
        log.debug('Committed database changes')

        return dict(
            result=dict(
                target=params['apptype'],
                project=project.name
            )
        )

    @validate('project')
    def promote(self, project, **params):
        """Deploy given version of given project to requested application
           tiers or hosts
        """

        log.debug('Deploying project')

        self.ensure_explicit_destinations(project, params)

        pkg_id, app_ids, app_host_map = self.get_app_info(project, params)

        if pkg_id is None:
            raise Exception(
                'Package "%s@%s" does not exist',
                project.name, params['version']
            )

        package = tds.model.Package.get(id=pkg_id)
        params['package_name'] = package.name

        app_dep_map = self.find_app_deployments(pkg_id, app_ids, params)

        app_host_map, app_dep_map = \
            self.determine_new_deployments(project, params, pkg_id, app_ids,
                                           app_host_map, app_dep_map)

        self.send_notifications(project, params)
        self.perform_deployments(
            project, params, pkg_id, app_host_map, app_dep_map
        )

        tagopsdb.Session.commit()
        log.debug('Committed database changes')

    @validate('project')
    def invalidate(self, project, **params):
        """Invalidate a given version of a given project"""

        log.debug('Invalidating for given project')

        # Not a deployment
        params['deployment'] = False

        self.ensure_explicit_destinations(project, params)

        target_names = list(x.name for x in project.targets)

        if params.get('apptypes', None) is not None:
            if not all(x in target_names for x in params['apptypes']):
                return dict(error=Exception(
                    'Valid deploy targets for project "%s" are: %r',
                    project.name,
                    map(str, target_names)
                ))

        pkg_id, app_ids, _app_host_map = self.get_app_info(project, params)
        if pkg_id is None:
            return dict(error=Exception(
                'Package "%s@%s" does not exist',
                project.name, params['version']
            ))

        app_dep_map = self.find_app_deployments(pkg_id, app_ids, params)

        if not len(filter(None, app_dep_map.itervalues())):
            log.info(
                'No deployments to invalidate for application %r '
                'with version %r in %s environment',
                project.name, params['version'],
                self.envs[params['environment']]
            )
            return

        app_dep_map = self.determine_invalidations(project, params, app_ids,
                                                   app_dep_map)
        self.perform_invalidations(app_dep_map)

        tagopsdb.Session.commit()
        log.debug('Committed database changes')

    @validate('project')
    def show(self, project, **params):
        """Show deployment information for a given project"""

        log.debug('Showing deployment information for given project')

        # Check apptypes, then filter if needed
        targets = []
        app_ids = self.get_app_types(project, params)

        if params.get('apptypes', None):
            for apptype in params['apptypes']:
                target = tds.model.DeployTarget.get(name=apptype)

                if target is None:
                    return dict(error=Exception(
                        'Apptype "%s" does not exist', apptype
                    ))

                if target.id not in app_ids:
                    return dict(error=Exception(
                        'Apptype "%s" does not map to project "%s"',
                        apptype, project.name
                    ))

                targets.append(target)
        else:
            targets = [
                x for x in tds.model.DeployTarget.all()
                if x.id in app_ids
            ]

        pkg_def_app_map = collections.defaultdict(list)

        for target in targets:
            for proj_pkg in tagopsdb.ProjectPackage.find(
                project_id=project.id, app_id=target.id
            ):
                pkg_def_app_map[proj_pkg.package_definition].append(target)

        # Find deployments
        deploy_info = []

        for pkg_def in pkg_def_app_map.keys():
            pkg_dep_info = dict(
                environment=params['environment'],
                package=pkg_def,
                by_apptype=[],
                by_hosts=[]
            )

            for target in pkg_def_app_map[pkg_def]:
                curr_app_dep = None
                prev_app_dep = None

                for package in pkg_def.packages:
                    prev_dep_candidates = []
                    curr_dep_candidates = []
                    for deployment in package.deployments:
                        for app_dep in deployment.app_deployments:
                            if app_dep.app_id != target.id:
                                continue

                            if app_dep.status == 'invalidated':
                                continue

                            curr_dep_candidates.append(app_dep)

                            if app_dep.status != 'validated':
                                continue

                            prev_dep_candidates.append(app_dep)

                    curr_dep_candidates.sort(key=lambda x: x.realized,
                                             reverse=True)
                    try:
                        curr_app_dep = curr_dep_candidates.pop(0)
                    except IndexError:
                        pass

                    if curr_app_dep in prev_dep_candidates:
                        prev_dep_candidates.remove(curr_app_dep)

                    prev_dep_candidates.sort(key=lambda x: x.realized,
                                             reverse=True)
                    try:
                        prev_app_dep = prev_dep_candidates.pop(0)
                    except IndexError:
                        pass

                pkg_dep_info['by_apptype'].append(dict(
                    apptype=target,
                    current_deployment=curr_app_dep,
                    previous_deployment=prev_app_dep
                ))

            # Skipping 'by_hosts' population for the moment

            deploy_info.append(pkg_dep_info)

        return dict(result=deploy_info)


    @validate('project')
    def rollback(self, project, **params):
        """Rollback to the previous validated deployed version of given
           project on requested application tiers or hosts
        """

        log.debug('Rolling back project')

        self.ensure_explicit_destinations(project, params)

        pkg_id, app_ids, app_host_map = self.get_app_info(project, params)
        app_dep_map = self.find_app_deployments(pkg_id, app_ids, params)

        if not len(filter(None, app_dep_map.itervalues())):
            log.info(
                'Nothing to roll back for application %r in %s '
                'environment', project.name,
                self.envs[params['environment']]
            )
            return

        # Save verison of application/deployment map for invalidation
        # at the end of the run
        log.log(5, 'Saving current application/deployment map')
        orig_app_dep_map = app_dep_map

        app_pkg_map, app_host_map, app_dep_map = \
            self.determine_rollbacks(params, app_ids, app_host_map,
                                     app_dep_map)
        self.send_notifications(project, params)
        self.perform_rollbacks(project, params, app_pkg_map, app_host_map, app_dep_map)

        if not params.get('hosts', None):
            # Now perform invalidations, commit immediately follows
            # Note this is only done for tiers
            self.perform_invalidations(orig_app_dep_map)

        tagopsdb.Session.commit()
        log.debug('Committed database changes')

    @staticmethod
    def get_package_for_target(target, environment):
        deployments = target.app_deployments
        dep = None
        for dep in sorted(deployments, key=lambda x: x.realized, reverse=True):
            if dep.environment != environment.environment:
                continue

            if dep.status in ('inprogress', 'incomplete'):
                return dict(error=Exception(
                    'Deploy target "%s" is being deployed to currently',
                    target.name
                ))

            if dep.status in ('complete', 'validated'):
                break
        else:
            dep = None

        if dep is not None:
            pkg = dep.deployment.package
            return pkg

        return None

    @validate('project')
    def restart(self, project, **params):
        """Restart given project on requested application tiers or hosts"""

        log.debug('Restarting application for project')

        # Not a deployment
        params['deployment'] = False

        self.ensure_explicit_destinations(project, params)

        environment = tagopsdb.Environment.get(env=params['environment'])

        apptypes = params.get('apptypes', None)
        hostnames = params.get('hosts', None)

        restart_targets = []

        if apptypes is not None or hostnames is None:
            if apptypes:
                targets = [
                    tds.model.DeployTarget.get(name=apptype)
                    for apptype in apptypes
                ]
            else:
                targets = project.targets

            for target in targets:
                if target is None or target not in project.targets:
                    return dict(error=Exception(
                        'Valid apptypes for project "%s" are: %s',
                        project.name, [str(x.name) for x in project.targets]
                    ))

                pkg = self.get_package_for_target(target, environment)
                if pkg is None:
                    continue

                for host in target.hosts:
                    if host.environment == environment.environment:
                        restart_targets.append((host, pkg))

        elif hostnames:
            app_ids = [x.id for x in project.targets]
            bad_hosts = []
            no_exist_hosts = []
            hosts = [
                tagopsdb.Host.get(name=hostname)
                for hostname in hostnames
            ]
            for host, hostname in zip(hosts, hostnames):
                if host is None:
                    no_exist_hosts.append(hostname)
                    continue

                if (
                    host.app_id not in app_ids or
                    host.environment != environment.environment
                ):
                    bad_hosts.append(hostname)

            if no_exist_hosts:
                return dict(error=Exception(
                    "These hosts do not exist: %s", ', '.join(no_exist_hosts)
                ))

            if bad_hosts:
                return dict(error=Exception(
                    'The following hosts are in the wrong environment or '
                    'do not belong to a matching app type: %s',
                    ', '.join(bad_hosts)
                ))

            for host in hosts:
                pkg = self.get_package_for_target(host.application, environment)
                if pkg is None:
                    continue

                restart_targets.append((host, pkg))

        if not restart_targets:
            return dict(error=Exception(
                'Nothing to restart for project "%s" in %s environment',
                project.name, environment.environment
            ))

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

    @validate('project')
    def redeploy(self, project, **params):
        """Redeploy given project to requested application tiers or hosts"""

        log.debug('Redeploying project')

        self.ensure_explicit_destinations(project, params)

        pkg_id, app_ids, app_host_map = self.get_app_info(project, params,
                                                          hostonly=True)
        app_dep_map = self.find_app_deployments(pkg_id, app_ids, params)

        if not len(filter(None, app_dep_map.itervalues())):
            log.info(
                'Nothing to redeploy for application %r in %s '
                'environment', project.name,
                self.envs[params['environment']]
            )
            return

        dep_id = self.determine_redeployments(pkg_id)
        self.send_notifications(project, params)
        self.perform_redeployments(project, params, dep_id, app_host_map, app_dep_map)

        tagopsdb.Session.commit()
        log.debug('Committed database changes')

    @validate('project')
    def validate(self, project, **params):
        """Validate a given version of a given project"""

        log.debug('Validating for given project')

        # Not a deployment
        params['deployment'] = False

        self.ensure_explicit_destinations(project, params)

        target_names = list(x.name for x in project.targets)

        if params.get('apptypes', None) is not None:
            if not all(x in target_names for x in params['apptypes']):
                return dict(error=Exception(
                    'Valid deploy targets for project "%s" are: %r',
                    project.name,
                    map(str, target_names)
                ))

        pkg_id, app_ids, _app_host_map = self.get_app_info(project, params)

        if pkg_id is None:
            return dict(error=Exception(
                'Package "%s@%s" does not exist',
                project.name, params['version']
            ))

        app_dep_map = self.find_app_deployments(pkg_id, app_ids, params)

        if not len(filter(None, app_dep_map.itervalues())):
            return dict(error=Exception(
                'No deployments to validate for application %r '
                'in %s environment', project.name,
                self.envs[params['environment']]
            ))

        app_dep_map = self.determine_validations(project, params, pkg_id, app_ids,
                                                 app_dep_map)
        self.perform_validations(project, params, app_dep_map)

        tagopsdb.Session.commit()
        log.debug('Committed database changes')
