import errno
import os
import os.path
import re
import signal
import socket
import subprocess
import sys
import time

from datetime import datetime, timedelta

import json
import progressbar

from tagopsdb.database.meta import Session
from tagopsdb.exceptions import RepoException, PackageException, \
                                DeployException, NotImplementedException

import tagopsdb.deploy.repo as repo
import tagopsdb.deploy.package as package
import tagopsdb.deploy.deploy as deploy

import tds.authorize
import tds.notifications
import tds.utils

from tds.exceptions import NoCurrentDeploymentError, NotImplementedError, \
                           WrongEnvironmentError, WrongProjectTypeError


def catch_exceptions(meth):
    """Catch common database library exceptions"""

    def wrapped(*args, **kwargs):
        try:
            val = meth(*args, **kwargs)
        except NotImplementedException, e:
            raise NotImplementedError(e)

        return val

    return wrapped


class Repository(object):
    """Commands to manage the deployment repository"""

    def __init__(self, logger):
        """Basic initialization"""

        self.log = logger


    @tds.utils.debug
    @catch_exceptions
    def add(self, params):
        """Add a given project to the repository"""

        self.log.debug('Adding application %r to repository',
                       params['project'])

        tds.authorize.verify_access(params['user_level'], 'admin')

        try:
            # For now, project_type is 'application'
            params['projecttype'] = 'application'
            project, project_new, pkg_def = \
                repo.add_app_location(params['projecttype'],
                                      params['buildtype'], params['pkgname'],
                                      params['project'], params['pkgpath'],
                                      params['arch'], params['buildhost'],
                                      params['env_specific'])
            self.log.debug(5, 'Application\'s Location ID is: %d',
                           project.id)

            self.log.debug('Mapping Location ID to various applications')
            repo.add_app_packages_mapping(project, project_new, pkg_def,
                                          params['apptypes'])
        except RepoException, e:
            self.log.error(e)
            return

        if params['config']:
            self.log.debug('Adding application %r to config project %r',
                           params['project'], params['config'])

            try:
                config = repo.find_app_location(params['config'])
                # Transitional code for refactoring
                config_new = repo.find_project(params['config'])
                config_def = package.find_package_definition(config_new.id)

                self.log.debug(5, 'Config project %r\'s Location ID is: %s',
                               params['config'], config.id)
                repo.add_app_packages_mapping(config, config_new, config_def,
                                              params['apptypes'])
            except RepoException, e:
                self.log.error(e)
                return

        Session.commit()
        self.log.debug('Committed database changes')


    @tds.utils.debug
    @catch_exceptions
    def delete(self, params):
        """Remove a given project from the repository"""

        self.log.debug('Removing application %r from repository',
                       params['project'])

        tds.authorize.verify_access(params['user_level'], 'admin')

        try:
            repo.delete_app_location(params['project'])
        except RepoException, e:
            self.log.error(e)
            return

        Session.commit()
        self.log.debug('Committed database changes')


    @tds.utils.debug
    @catch_exceptions
    def list(self, params):
        """Show information for requested projects (or all projects)"""

        self.log.debug('Listing information for requested application(s) '
                       'in the repository')

        tds.authorize.verify_access(params['user_level'], 'dev')

        apps = repo.list_app_locations(params['projects'])

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
            app_defs = repo.find_app_packages_mapping(app.app_name)
            app_types = sorted([ x.app_type for x in app_defs ])
            self.log.info('App types: %s', ', '.join(app_types))

            if app.environment:
                is_env = 'Yes'
            else:
                is_env = 'No'

            self.log.info('Environment specific: %s', is_env)
            self.log.info('')

        return apps


class Package(object):
    """Commands to manage packages for supported applications"""

    def __init__(self, logger):
        """Basic initialization"""

        self.host = socket.gethostname()
        self.log = logger


    def processing_handler(self, signum, frame):
        """This handler is called if the file in the incoming or processing
           directory is not removed in a given amount of time, meaning the
           repository server had a failure.
        """

        raise PackageException('The file placed in the incoming or '
                               'processing queue was not removed.\n'
                               'Please contact SiteOps for assistance.')


    def wait_for_file_removal(self, path):
        """Wait until a given file has been removed"""

        while True:
            try:
                # The listdir() is necessary due to NFS cache
                # timeouts - the stat() will trigger the exception
                # once the file itself is gone
                os.listdir(os.path.dirname(path))
                os.stat(path)
                time.sleep(0.5)
            except OSError, e:
                if e.errno == errno.ENOENT:
                    break


    def _queue_rpm(self, params, queued_rpm, rpm_name, app):
        """Move requested RPM into queue for processing"""

        # Verify required RPM exists and create hard link into
        # the incoming directory for the repository server to find
        build_base = params['repo']['build_base']
        src_rpm = os.path.join(build_base, app.path, rpm_name)
        self.log.debug(5, 'Source RPM is: %s', src_rpm)

        self.log.info('Checking for existence of file "%s"...', src_rpm)

        if not os.path.isfile(src_rpm):
            self.log.info('File "%s" is not found in "%s"',
                          src_rpm, build_base)
            return False

        try:
            self.log.info('Build host "%s" built RPM successfully',
                          app.build_host)
            self.log.info('Linking RPM into incoming directory...')
            os.link(src_rpm, queued_rpm)
        except Exception, e:   # Really need to narrow the exception down
            self.log.error(e)
            return False

        self.log.info('RPM successfully linked')
        return True


    @tds.utils.debug
    @catch_exceptions
    def add(self, params):
        """Add a given version of a package for a given project"""

        self.log.debug('Adding version %s of the package for project "%s" '
                       'to software repository', params['version'],
                       params['project'])

        tds.authorize.verify_access(params['user_level'], 'dev')

        try:
            # The real 'revision' is hardcoded to 1 for now
            # This needs to be changed at some point
            package.add_package(params['project'], params['version'], '1',
                                params['user'])
        except PackageException, e:
            self.log.error(e)
            return

        # Get repo information for package
        app = repo.find_app_location(params['project'])

        # Revision hardcoded for now
        rpm_name = '%s-%s-1.%s.rpm' % (app.pkg_name, params['version'],
                                       app.arch)
        incoming_dir = params['repo']['incoming']
        processing_dir = params['repo']['processing']

        queued_rpm = os.path.join(incoming_dir, rpm_name)
        self.log.debug(5, 'Queued RPM is: %s', queued_rpm)
        process_rpm = os.path.join(processing_dir, rpm_name)
        self.log.debug(5, 'Processed RPM is: %s', process_rpm)

        if not self._queue_rpm(params, queued_rpm, rpm_name, app):
            return

        # wait until file has been removed or timeout with
        # error (meaning repository side failed, check logs there)

        self.log.info('Waiting for software repository server')
        self.log.info('  to update deploy repo...')

        self.log.debug(5, 'Setting up signal handler')
        signal.signal(signal.SIGALRM, self.processing_handler)
        signal.alarm(120)

        self.log.debug(5, 'Waiting for RPM to be removed from queued '
                       'directory')
        self.wait_for_file_removal(queued_rpm)
        self.log.debug(5, 'Waiting for RPM to be removed from processing '
                       'directory')
        self.wait_for_file_removal(process_rpm)

        signal.alarm(0)
        self.log.info('Repository successfully updated')

        Session.commit()
        self.log.debug('Committed database changes')

        self.log.info('Added package for project "%s", version %s',
                      params['project'], params['version'])


    @tds.utils.debug
    @catch_exceptions
    def delete(self, params):
        """Delete a given version of a package for a given project"""

        self.log.debug('Deleting version %s of the package for project "%s" '
                       'from software repository', params['version'],
                       params['project'])

        tds.authorize.verify_access(params['user_level'], 'dev')

        try:
            # The real 'revision' is hardcoded to 1 for now
            # This needs to be changed at some point
            package.delete_package(params['project'], params['version'], '1')
        except PackageException, e:
            self.log.error(e)
            return

        Session.commit()
        self.log.debug('Committed database changes')


    @tds.utils.debug
    @catch_exceptions
    def list(self, params):
        """Show information for all existing packages in the software
           repository for requested projects (or all projects)
        """

        if params['projects'] is None:
            apps = 'ALL'
        else:
            apps = ', '.join(params['projects'])

        self.log.debug('Listing information for all existing packages '
                       'for projects: %s', apps)

        tds.authorize.verify_access(params['user_level'], 'dev')

        packages_sorted = sorted(package.list_packages(params['projects']),
                                 key=lambda pkg: int(pkg.version))

        for pkg in packages_sorted:
            self.log.info('Project: %s', pkg.pkg_name)
            self.log.info('Version: %s', pkg.version)
            self.log.info('Revision: %s', pkg.revision)
            self.log.info('')


class Jenkinspackage(Package):
    """Temporary class to manage packages for supported applications
       via direct access to Jenkins build (artifactory)
    """

    def _queue_rpm(self, params, queued_rpm, rpm_name, app):
        """Move requested RPM into queue for processing"""

        buildnum = int(params['version'])
        job_name = params['job_name']

        # Late import to prevent hard dependency
        from jenkinsapi.jenkins import Jenkins
        from jenkinsapi.exceptions import JenkinsAPIException, NotFound

        J = Jenkins('https://ci.tagged.com/')   #TODO: use config

        try:
            a = J[job_name].get_build(buildnum).get_artifact_dict()[rpm_name]
            data = a.get_data()
        except (JenkinsAPIException, KeyError, NotFound) as e:
            self.log.error(e)
            return False

        tmpname = os.path.join(os.path.dirname(os.path.dirname(queued_rpm)),
                               'tmp', rpm_name)

        with open(tmpname, 'wb') as f:
            f.write(data)
            f.close()
            os.link(f.name, queued_rpm)
            os.unlink(f.name)

        return True


class BaseDeploy(object):
    """Common methods for the config and deploy commands"""

    dep_types = { 'promote' : 'Deployment',
                  'redeploy' : 'Redeployment',
                  'rollback' : 'Rollback',
                  'push' : 'Push',
                  'repush' : 'Repush',
                  'revert' : 'Reversion', }
    envs = { 'dev' : 'development',
             'stage' : 'staging',
             'prod' : 'production', }
    env_order = [ 'dev', 'stage', 'prod' ]


    def __init__(self, logger):
        """Basic initialization"""

        self.valid_project_types = None
        self.log = logger


    @tds.utils.debug
    def check_for_current_deployment(self, params, app_id, hosts=None):
        """For the current app type, see if there are any current deployments
           running and notify if there is
        """

        self.log.debug('Checking for a deployment of the same application '
                       'already in progress')

        time_delta = timedelta(hours=1)  # Harcoded to an hour for now
        self.log.debug(5, 'time_delta is: %s', time_delta)

        dep_info = deploy.find_running_deployment(app_id,
                                       self.envs[params['environment']],
                                       hosts=hosts)

        if dep_info:
            self.log.debug('Current deployment found')

            dep_type, data = dep_info
            self.log.debug(5, 'Deployment type is: %s', dep_type)

            if dep_type == 'tier':
                dep_user, dep_realized, dep_env, dep_apptype = data
                self.log.debug(5, 'Deployment user is: %s', dep_user)
                self.log.debug(5, 'Deployment realized is: %s', dep_realized)
                self.log.debug(5, 'Deployment environment is: %s', dep_env)
                self.log.debug(5, 'Deployment apptype is: %s', dep_apptype)

                if datetime.now() - dep_realized < time_delta:
                    self.log.info('User "%s" is currently running a '
                                  'deployment for the %s app tier in the %s '
                                  'environment, skipping...',
                                  dep_user, dep_apptype, dep_env)
                    return True
            else:   # dep_type is 'host'
                dep_hosts = []

                for entry in data:
                    dep_user, dep_realized, dep_hostname, dep_env = entry
                    self.log.debug(5, 'Deployment user is: %s', dep_user)
                    self.log.debug(5, 'Deployment realized is: %s',
                                   dep_realized)
                    self.log.debug(5, 'Deployment hostname is: %s',
                                   dep_hostname)
                    self.log.debug(5, 'Deployment environment is: %s',
                                   dep_env)

                    if datetime.now() - dep_realized < time_delta:
                        self.log.debug(5, 'Host %r active with deployment',
                                       dep_hostname)
                        dep_hosts.append(dep_hostname)

                if dep_hosts:
                    # Allow separate hosts to get simultaneous deployments
                    if (hosts is None or
                        not set(dep_hosts).isdisjoint(set(hosts))):
                        host_list = ', '.join(dep_hosts)
                        self.log.info('User "%s" is currently running a '
                                      'deployment for the hosts "%s" in '
                                      'the %s environment, skipping...',
                                      dep_user, host_list, dep_env)
                        return True

        self.log.debug('No current deployment found')
        return False


    @tds.utils.debug
    def check_tier_state(self, params, pkg_id, app_dep):
        """Ensure state of tier (from given app deployment) is consistent
           with state and deployment package versions
        """

        self.log.debug('Checking state of tier')

        apptype_hosts = deploy.find_hosts_for_app(app_dep.app_id,
                                          self.envs[params['environment']])
        apptype_hostnames = [ x.hostname for x in apptype_hosts ]
        self.log.debug(5, 'Tier hosts are: %s', ', '.join(apptype_hostnames))

        dep_hosts = \
            deploy.find_host_deployments_by_package_name(params['project'],
                                                         apptype_hostnames)
        dep_hostnames = [ x.hostname for x in dep_hosts ]

        if dep_hostnames:
            self.log.debug(5, 'Deployed hosts are: %s',
                           ', '.join(dep_hostnames))

        missing_deps = list(set(apptype_hostnames) - set(dep_hostnames))
        version_diffs = [ x.hostname for x in dep_hosts
                          if int(x.version) != params['version'] ]

        if version_diffs:
            self.log.debug(5, 'Version differences on: %s',
                           ', '.join(version_diffs))

        not_ok_hosts = deploy.find_host_deployments_not_ok(pkg_id,
                              app_dep.app_id,
                              self.envs[params['environment']])
        not_ok_hostnames = [ x.hostname for x in not_ok_hosts ]

        if not_ok_hostnames:
            self.log.debug(5, 'Hosts with failed deployments are: %s',
                           ', '.join(not_ok_hostnames))

        if (missing_deps or version_diffs or not_ok_hosts):
            return ('failed', missing_deps, version_diffs, not_ok_hostnames)
        else:
            return ('ok', [], [], [])


    @tds.utils.debug
    def create_notifications(self, params):
        """Create subject and message for a notification"""

        self.log.debug('Creating information for notifications')

        # Determine version
        if 'version' in params:
            version = params['version']
        elif 'current_version' in params:
            version = params['current_version']
        else:
            version = 'unknown'   # This should never happen

        self.log.debug(5, 'Application version is: %s', version)

        dep_type = self.dep_types[params['subcommand_name']]

        if params.get('hosts', None):
            dest_type = 'hosts'
            destinations = ', '.join(params['hosts'])
        elif params.get('apptypes', None):
            dest_type = 'app tier(s)'
            destinations = ', '.join(params['apptypes'])
        else:
            dest_type = 'app tier(s)'
            destinations = ', '.join([ x.app_type for x in
                repo.find_app_packages_mapping(params['project']) ])

        self.log.debug(5, 'Destination type is: %s', dest_type)
        self.log.debug(5, 'Destinations are: %s', destinations)

        msg_subject = '%s of version %s of %s on %s %s in %s' \
                      % (dep_type, version, params['project'], dest_type,
                         destinations, self.envs[params['environment']])
        msg_text = '%s performed a "tds %s %s" for the following %s ' \
                   'in %s:\n    %s' \
                   % (params['user'], params['command_name'],
                      params['subcommand_name'], dest_type,
                      self.envs[params['environment']], destinations)

        return msg_subject, msg_text


    @tds.utils.debug
    def deploy_to_host(self, dep_host, app, version, retry=4):
        """Deploy specified package to a given host"""

        self.log.debug('Deploying to host %r' % dep_host)

        mco_cmd = [ '/usr/bin/mco', 'tds', '--discovery-timeout', '4',
                    '--timeout', '60', '-W', 'hostname=%s' % dep_host,
                    app, version ]

        return self.process_mco_command(mco_cmd, retry)


    @tds.utils.debug
    def deploy_to_hosts(self, params, dep_hosts, dep_id, redeploy=False):
        """Perform deployment on given set of hosts (only doing those
           that previously failed with a redeploy)
        """

        self.log.debug('Performing host deployments')

        total_hosts = len(dep_hosts)
        host_count = 1
        failed_hosts = []

        # widgets for progress bar
        widgets = [ 'Completed: ', progressbar.Counter(),
                    ' out of %d hosts' % total_hosts,
                    ' (', progressbar.Timer(), ', ', progressbar.ETA(), ')' ]

        if params['verbose'] is None:
            pbar = progressbar.ProgressBar(widgets=widgets,
                                           maxval=total_hosts).start()

        for dep_host in sorted(dep_hosts, key=lambda host: host.hostname):
            pkg = deploy.find_app_by_depid(dep_id)
            app, version = pkg.pkg_name, pkg.version
            self.log.debug(5, 'Project name and version: %s %s', app, version)

            host_dep = deploy.find_host_deployment_by_depid(dep_id,
                                                            dep_host.hostname)

            if redeploy and host_dep and host_dep.status != 'ok':
                self.log.debug(5, 'Host %r needs redeloyment',
                               dep_host.hostname)
                success, info = self.deploy_to_host(dep_host.hostname, app,
                                                    version)

                if success:
                    self.log.debug(5, 'Deployment to host %r successful',
                                   dep_host.hostname)

                    # Commit to DB immediately
                    host_dep.status = 'ok'
                    Session.commit()

                    self.log.debug(5, 'Committed database (nested) change')
                else:
                    self.log.debug(5, 'Deployment to host %r failed',
                                   dep_host.hostname)
                    failed_hosts.append((dep_host.hostname, info))
            else:
                if host_dep and host_dep.status == 'ok':
                    self.log.info('Host %r already has version "%s" of '
                                  'application %r successfully deployed, '
                                  'skipping', dep_host.hostname, version, app)
                    continue

                # Clear out any old deployments for this host
                self.log.debug(5, 'Deleting any old deployments for host %r',
                               dep_host.hostname)
                deploy.delete_host_deployment(dep_host.hostname,
                                              params['project'])
                host_dep = deploy.add_host_deployment(dep_id, dep_host.id,
                                                      params['user'],
                                                      'inprogress')
                success, info = self.deploy_to_host(dep_host.hostname, app,
                                                    version)

                if success:
                    self.log.debug(5, 'Deployment to host %r successful',
                                   dep_host.hostname)

                    # Commit to DB immediately
                    host_dep.status = 'ok'
                    Session.commit()
                else:
                    self.log.debug(5, 'Deployment to host %r failed',
                                   dep_host.hostname)

                    # Commit to DB immediately
                    host_dep.status = 'failed'
                    Session.commit()

                    failed_hosts.append((dep_host.hostname, info))

                self.log.debug(5, 'Committed database (nested) change')

            if params['verbose'] is None:
                pbar.update(host_count)

            host_count += 1

            if params['delay']:
                self.log.debug(5, 'Sleeping for %d seconds...',
                               params['delay'])
                time.sleep(params['delay'])

        if params['verbose'] is None:
            pbar.finish()

        # If any hosts failed, show failure information for each
        if failed_hosts:
            self.log.info('Some hosts had failures:\n')

            for failed_host, reason in failed_hosts:
                self.log.info('-----')
                self.log.info('Hostname: %s', failed_host)
                self.log.info('Reason: %s', reason)

            return False
        else:
            return True


    @tds.utils.debug
    def deploy_to_hosts_or_tiers(self, params, dep_id, app_host_map,
                                 app_dep_map, redeploy=False):
        """Do the deployment to the requested hosts or application tiers"""

        self.log.debug('Deploying to requested hosts or application tiers')

        app_ids = []

        if params.get('hosts', None):
            self.log.debug(5, 'Deployment is for hosts...')

            for app_id, hosts in app_host_map.iteritems():
                if self.check_for_current_deployment(params, app_id,
                                                     hosts=hosts):
                    self.log.debug(5, 'App ID %s already has deployment, '
                                   'skipping...', app_id)
                    continue

                app_ids.append(app_id)

                self.log.debug(5, 'Hosts being deployed to are: %s',
                               ', '.join(hosts))
                dep_hosts = [ deploy.find_host_by_hostname(x) for x in hosts ]

                # We want the tier status updated only if doing
                # a rollback
                if self.deploy_to_hosts(params, dep_hosts, dep_id,
                                        redeploy=redeploy) \
                    and params['subcommand_name'] == 'rollback':
                    app_dep = app_dep_map[app_id][0]
                    app_dep.status = 'complete'
        else:
            self.log.debug(5, 'Deployment is for application tiers...')

            for app_id, dep_info in app_dep_map.iteritems():
                if self.check_for_current_deployment(params, app_id):
                    self.log.debug(5, 'App ID %s already has deployment, '
                                   'skipping...', app_id)
                    continue

                app_ids.append(app_id)

                if redeploy:
                    app_dep, app_type, dep_type, pkg = dep_info

                    # Don't redeploy to a validated tier
                    if app_dep.status == 'validated':
                        self.log.info('Application "%s" with version "%s" '
                                      'already validated on app type %s"',
                                      params['project'], pkg.version,
                                      app_type)
                        continue
                else:
                    app_dep = deploy.add_app_deployment(dep_id, app_id,
                                             params['user'], 'inprogress',
                                             self.envs[params['environment']])

                dep_hosts = deploy.find_hosts_for_app(app_id,
                                        self.envs[params['environment']])

                if self.deploy_to_hosts(params, dep_hosts, dep_id,
                                        redeploy=redeploy):
                    app_dep.status = 'complete'
                else:
                    app_dep.status = 'incomplete'

                self.log.debug(5, 'Setting deployment status to: %s',
                               app_dep.status)

        if params['environment'] == 'prod':
            self.log.info('Please review the following Nagios group views '
                          'or the deploy health status:')

            for app_id in app_ids:
                app_type = deploy.find_apptype_by_appid(app_id)
                self.log.info('  https://nagios.tagged.com/nagios/cgi-bin/'
                              'status.cgi?style=detail&hostgroup=app.%s',
                              app_type)


    @tds.utils.debug
    def determine_invalidations(self, params, app_ids, app_dep_map):
        """Determine which application tiers need invalidations performed"""

        self.log.debug('Determining invalidations for requested application '
                       'types')

        curr_deps = deploy.find_latest_deployed_version(params['project'],
                                       self.envs[params['environment']],
                                       apptier=True)
        curr_dep_versions = {}

        for app_type, version, revision in curr_deps:
            self.log.debug(5, 'App type: %s, Version: %s, Revision %s',
                           app_type, version, revision)
            curr_dep_versions[app_type] = int(version)

        for app_id in app_ids:
            if not app_dep_map[app_id]:
                self.log.debug(5, 'Application ID %r is not in deployment/'
                               'application map', app_id)
                continue

            ok = True

            app_dep, app_type, dep_type, pkg = app_dep_map[app_id]
            self.log.debug(5, 'Application deployment is: %r', app_dep)
            self.log.debug(5, 'Application type is: %s', app_type)
            self.log.debug(5, 'Deployment type is: %s', dep_type)
            self.log.debug(5, 'Package is: %r', pkg)

            # Ensure version to invalidate isn't the current
            # deployment for this app type
            if curr_dep_versions.get(app_type, None) == params['version']:
                self.log.info('Unable to invalidate application "%s" with '
                              'version "%s" for apptype "%s" as that version '
                              'is currently deployed for the apptype',
                              params['project'], params['version'], app_type)
                ok = False

            if ok:
                if app_dep.status != 'validated':
                    self.log.info('Deployment for application "%s" with '
                                  'version "%s" for apptype "%s" has not '
                                  'been validated in %s environment',
                                  params['project'], params['version'],
                                  app_type, self.envs[params['environment']])
                    ok = False

            if not ok:
                self.log.debug(5, 'Deleting application ID %r from '
                               'deployment/application map', app_id)
                del app_dep_map[app_id]

        self.log.debug(5, 'Deployment/application map is: %r', app_dep_map)

        return app_dep_map


    @tds.utils.debug
    def determine_new_deployments(self, params, pkg_id, app_ids, app_host_map,
                                  app_dep_map):
        """Determine which application tiers or hosts need new deployments"""

        self.log.debug('Determining deployments for requested application '
                       'types or hosts')

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
            ok = self.check_previous_environment(params, pkg_id, app_id)

            if ok:
                if not app_dep_map[app_id]:
                    self.log.debug(5, 'Application ID %r is not in '
                                   'deployment/application map', app_id)
                    continue

                app_dep, app_type, dep_type, pkg = app_dep_map[app_id]
                self.log.debug(5, 'Application deployment is: %r', app_dep)
                self.log.debug(5, 'Application type is: %s', app_type)
                self.log.debug(5, 'Deployment type is: %s', dep_type)
                self.log.debug(5, 'Package is: %r', pkg)

                if (app_dep.status != 'invalidated' and dep_type == 'deploy'
                    and pkg.version == params['version']):
                    self.log.info('Application %r with version "%s" '
                                  'already deployed to this environment (%s) '
                                  'for apptype %r',
                                  params['project'], params['version'],
                                  self.envs[params['environment']], app_type)
                    ok = False

            if not ok:
                if params.get('hosts', None):
                    self.log.debug(5, 'Deleting application ID %r from '
                                   'host/application map', app_id)
                    del app_host_map[app_id]
                else:
                    self.log.debug(5, 'Deleting application ID %r from '
                                   'deployment/application map', app_id)
                    del app_dep_map[app_id]

        self.log.debug(5, 'Host/application map is: %r', app_host_map)
        self.log.debug(5, 'Deployment/application map is: %r', app_dep_map)

        return (app_host_map, app_dep_map)


    @tds.utils.debug
    def determine_redeployments(self, pkg_id):
        """Determine which application tiers or hosts need redeployments"""

        self.log.debug('Determining redeployments for requested application '
                       'types or hosts')

        pkg_deps = deploy.find_deployment_by_pkgid(pkg_id)
        last_pkg_dep = pkg_deps[0]  # Guaranteed to have at least one

        return last_pkg_dep.id


    @tds.utils.debug
    def determine_restarts(self, pkg_id):
        """Determine which application tiers or hosts need restarts"""

        self.log.debug('Determining restarts for requested application '
                       'types or hosts')

        pkg_deps = deploy.find_deployment_by_pkgid(pkg_id)
        last_pkg_dep = pkg_deps[0]  # Guaranteed to have at least one

        return last_pkg_dep.id


    @tds.utils.debug
    def determine_rollbacks(self, params, app_ids, app_host_map, app_dep_map):
        """Determine which application tiers or hosts need rollbacks"""

        self.log.debug('Determining rollbacks for requested application '
                       'types or hosts')

        app_pkg_map = {}

        for app_id in app_ids:
            if not app_dep_map[app_id]:
                self.log.debug(5, 'Application ID %r is not in '
                               'deployment/application map', app_id)
                continue

            ok = True

            if params.get('hosts', None):
                prev_dep_info = \
                    deploy.find_latest_validated_deployment(
                                            params['project'], app_id,
                                            self.envs[params['environment']])
            else:
                prev_dep_info = \
                    deploy.find_previous_validated_deployment(
                                            params['project'], app_id,
                                            self.envs[params['environment']])

            if prev_dep_info is None:
                self.log.info('No previous deployment to roll back to for '
                              'application "%s" for app type "%s" in %s '
                              'environment', params['project'], app_id,
                              self.envs[params['environment']])
                ok = False
            else:
                prev_app_dep, prev_pkg_id = prev_dep_info
                self.log.debug(5, 'Previous application deployment is: %r',
                               prev_app_dep)
                self.log.debug(5, 'Previous package ID is: %s', prev_pkg_id)

                app_pkg_map[app_id] = prev_pkg_id

            if not ok:
                self.log.debug(5, 'Deleting application ID %r from '
                               'deployment/application map', app_id)
                del app_dep_map[app_id]

        self.log.debug(5, 'Package/application map is: %r', app_pkg_map)
        self.log.debug(5, 'Host/application map is: %r', app_host_map)
        self.log.debug(5, 'Deployment/application map is: %r', app_dep_map)

        return (app_pkg_map, app_host_map, app_dep_map)


    @tds.utils.debug
    def determine_validations(self, params, pkg_id, app_ids, app_dep_map):
        """Determine which application tiers need validation performed"""

        for app_id in app_ids:
            if not app_dep_map[app_id]:
                self.log.debug(5, 'Application ID %r is not in '
                               'deployment/application map', app_id)
                continue

            ok = True

            app_dep, app_type, dep_type, pkg = app_dep_map[app_id]
            self.log.debug(5, 'Application deployment is: %r', app_dep)
            self.log.debug(5, 'Application type is: %s', app_type)
            self.log.debug(5, 'Deployment type is: %s', dep_type)
            self.log.debug(5, 'Package is: %r', pkg)

            if app_dep.status == 'validated':
                self.log.info('Deployment for application %r for apptype %r '
                              'already validated in %s environment',
                              params['project'], app_type,
                              self.envs[params['environment']])
                ok = False

            if ok:
                # Ensure tier state is consistent
                result, missing, diffs, not_ok_hostnames = \
                    self.check_tier_state(params, pkg_id, app_dep)

                if result != 'ok':
                    self.log.info('Encountered issues while validating '
                                  'version %r of application %r:',
                                  params['version'], params['project'])

                    if missing:
                        self.log.info('  Hosts missing deployments of given '
                                      'version:')
                        self.log.info('    %s', ', '.join(missing))

                    if diffs:
                        self.log.info('  Hosts with different versions than '
                                      'the one being validated:')
                        self.log.info('    %s', ', '.join(diffs))

                    if not_ok_hostnames:
                        self.log.info('  Hosts not in an "ok" state:')
                        self.log.info('    %s', ', '.join(not_ok_hostnames))

                    if params['force']:
                        self.log.info('The "--force" option was used, '
                                      'validating regardless')
                        ok = True
                    else:
                        self.log.info('Rejecting validation, please use '
                                      '"--force" if you still want to '
                                      'validate')
                        ok = False

            if not ok:
                self.log.debug(5, 'Deleting application ID %r from '
                               'deployment/application map', app_id)
                del app_dep_map[app_id]

        self.log.debug(5, 'Deployment/application map is: %r', app_dep_map)

        return app_dep_map


    @tds.utils.debug
    def ensure_explicit_destinations(self, params):
        """Make sure multiple application types are explicit"""

        self.log.debug('Ensuring multiple application types are explicitly '
                       'mentioned')

        if not params['explicit'] and len(self.get_app_types(params)) > 1:
            self.log.info('Application "%s" has multiple corresponding '
                          'app types, please use "--apptypes" or '
                          '"--all-apptypes"', params['project'])
            sys.exit(1)


    @tds.utils.debug
    def ensure_newer_versions(self, params):
        """Ensure version being deployed is more recent than
           the currently deployed versions on requested app types
        """

        self.log.debug('Ensuring version to deploy is newer than the '
                       'currently deployed version')

        newer_versions = []
        dep_versions = deploy.find_latest_deployed_version(params['project'],
                              self.envs[params['environment']], apptier=True)

        for dep_app_type, dep_version, dep_revision in dep_versions:
            if params['apptypes'] and dep_app_type not in params['apptypes']:
                continue

            self.log.debug(5, 'Deployment application type is: %s',
                           dep_app_type)
            self.log.debug(5, 'Deployment version is: %s', dep_version)
            self.log.debug(5, 'Deployment revision is: %s', dep_revision)

            # Currently not using revision (always '1' at the moment)
            # 'dep_version' must be typecast to an integer as well,
            # since the DB stores it as a string - may move away from
            # integers for versions in the future, so take note here
            if params['version'] < int(dep_version):
                self.log.debug(5, 'Deployment version %r is newer than '
                               'requested version %r', dep_version,
                               params['version'])
                newer_versions.append(dep_app_type)

        if newer_versions:
            app_type_list = ', '.join(['"%s"' % x for x in newer_versions])
            self.log.info('Application %r for app types %s have newer '
                          'versions deployed than the requested version %r',
                          params['project'], app_type_list, params['version'])
            return False

        return True


    @tds.utils.debug
    def find_app_deployments(self, pkg_id, app_ids, params):
        """Find all relevant application deployments for the requested
        app types and create an application/deployment mapping,
        keeping track of which app types have a current deployment
        and which don't
        """

        self.log.debug('Finding all relevant application deployments')

        deps = deploy.find_app_deployment(pkg_id, app_ids,
                                          self.envs[params['environment']])

        app_dep_map = {}

        for app_id in app_ids:
            app_dep_map[app_id] = None

        for app_dep, app_type, dep_type, pkg in deps:
            self.log.debug(5, 'Application deployment is: %r', app_dep)
            self.log.debug(5, 'Application type is: %s', app_type)
            self.log.debug(5, 'Deployment type is: %s', dep_type)
            self.log.debug(5, 'Package is: %r', pkg)

            app_dep_map[app_dep.app_id] = (app_dep, app_type, dep_type, pkg)

        self.log.debug(5, 'Deployment/application map is: %r', app_dep_map)

        return app_dep_map


    @tds.utils.debug
    def get_app_info(self, params, hostonly=False):
        """Verify requested package and which hosts or app tiers
        to install the package; for hosts a mapping is kept between
        them and their related app types
        """

        self.log.debug('Verifying requested package is correct for given '
                       'application tiers or hosts')

        if params.get('hosts', None):
            self.log.debug(5, 'Verification is for hosts...')

            try:
                pkg_id, app_host_map = self.verify_package(params,
                                                           hostonly=hostonly)
            except ValueError, e:
                self.log.error('%s for given project and hosts', e)
                sys.exit(1)

            host_deps = deploy.find_host_deployments_by_package_name(
                                         params['project'], params['hosts'])

            for host_dep, hostname, app_id, dep_version in host_deps:
                self.log.debug(5, 'Host deployment is: %r', host_dep)
                self.log.debug(5, 'Hostname is: %s', hostname)
                self.log.debug(5, 'Application ID is: %s', app_id)
                self.log.debug(5, 'Deployment version is: %s', dep_version)

                curr_version = params.get('version', dep_version)
                self.log.debug(5, 'Current version is: %s', curr_version)

                if (params['subcommand_name'] != 'rollback'
                    and dep_version == curr_version
                    and host_dep.status == 'ok' and params['deployment']):
                    self.log.info('Application %r with version %r already '
                                  'deployed to host %r', params['project'],
                                  curr_version, hostname)
                    app_host_map[app_id].remove(hostname)

                    if not app_host_map[app_id]:
                        self.log.debug(5, 'Application ID %r is not in '
                                       'host/application map', app_id)
                        del app_host_map[app_id]

            app_ids = app_host_map.keys()
        else:
            self.log.debug(5, 'Verification is for application tiers...')

            try:
                pkg_id, app_ids = self.verify_package(params)
            except ValueError, e:
                self.log.error('%s for given project and application tiers',
                               e)
                sys.exit(1)

            app_host_map = None   # No need for this for tiers

        self.log.debug(5, 'Package ID is: %s', pkg_id)
        self.log.debug(5, 'Application IDs are: %s',
                       ', '.join([ str(x) for x in app_ids ]))
        self.log.debug(5, 'Host/application map is: %r', app_host_map)

        return (pkg_id, app_ids, app_host_map)


    @tds.utils.debug
    def get_app_types(self, params):
        """Determine application IDs for deployment"""

        self.log.debug('Determining the application IDs for deployment')

        try:
            app_ids = [ x.id for x
                        in repo.find_app_packages_mapping(params['project']) ]
            self.log.debug(5, 'Application IDs for projects are: %s',
                           ', '.join([ str(x) for x in app_ids ]))
        except RepoException, e:
            self.log.error(e)
            sys.exit(1)

        if params['apptypes']:
            try:
                app_defs = [ deploy.find_app_by_apptype(x)
                             for x in params['apptypes'] ]
                self.log.debug(5, 'Definitions for applications types are: '
                               '%s', ', '.join([ repr(x) for x in app_defs ]))
            except DeployException, e:
                self.log.error(e)
                sys.exit(1)

            new_app_ids = [ x.id for x in app_defs ]
            self.log.debug(5, 'Application IDs for given defintions are: %s',
                           ', '.join([ str(x) for x in new_app_ids ]))

            if set(new_app_ids).issubset(set(app_ids)):
                app_ids = new_app_ids
            else:
                self.log.info('One of the app types given is not a valid app '
                              'type for the current deployment')
                sys.exit(1)

        self.log.debug(5, 'Final application IDs are: %s',
                       ', '.join([ str(x) for x in app_ids ]))

        return app_ids


    @tds.utils.debug
    def get_package_id(self, params, app_ids, hostonly=False):
        """Get the package ID for the current project and version
           (or most recent deployed version if none is given) for
           a given set of application types
        """

        self.log.debug('Determining package ID for given project')

        app_types = [ deploy.find_apptype_by_appid(x) for x in app_ids ]
        self.log.debug(5, 'Application types are: %s', ', '.join(app_types))

        if 'version' in params:
            self.log.debug(5, 'Using given version %r for package',
                           params['version'])
            version = params['version']
        else:
            self.log.debug(5, 'Determining version for package')

            # Must determine latest deployed version(s);
            # they must all use the same package version
            # (Tuple of app_type, version, revision returned
            #  with DB query)
            apptier = not hostonly
            last_deps = deploy.find_latest_deployed_version(params['project'],
                               self.envs[params['environment']],
                               apptier=apptier)
            self.log.debug(5, 'Latest validated deployments: %r', last_deps)

            if hostonly:
                versions = [ x.version for x in last_deps
                             if x.id in app_ids ]
            else:
                versions = [ x.version for x in last_deps
                             if x.appType in app_types ]

            self.log.debug(5, 'Found versions are: %s', ', '.join(versions))

            if not versions:
                self.log.info('Application "%s" has no current tier/host '
                              'deployments to verify for the given apptypes/'
                              'hosts', params['project'])
                sys.exit(1)

            if not all(x == versions[0] for x in versions):
                raise ValueError('Multiple versions not allowed')

            version = versions[0]
            self.log.debug(5, 'Determined version is: %s', version)
            params['current_version'] = version   # Used for notifications

        try:
            # Revision hardcoded to '1' for now
            pkg = package.find_package(params['project'], version, '1')
            if not pkg:
                self.log.info('Application "%s" with version "%s" not '
                              'available in the repository.',
                              params['project'], version)
                sys.exit(1)
        except PackageException, e:
            self.log.error(e)
            sys.exit(1)

        self.log.debug(5, 'Package ID is: %s', pkg.id)

        return pkg.id


    @tds.utils.debug
    def get_previous_environment(self, curr_env):
        """Find the previous environment to the current one"""

        self.log.debug('Determining previous deployment environment')

        # Done this way since negative indexes are allowed
        if curr_env == 'dev':
            raise WrongEnvironmentError('There is no environment before '
                                        'the current environment (%s)'
                                        % curr_env)

        try:
            return self.env_order[self.env_order.index(curr_env) - 1]
        except ValueError:
            raise WrongEnvironmentError('Invalid environment: %s' % curr_env)


    @tds.utils.debug
    def perform_deployments(self, params, pkg_id, app_host_map, app_dep_map):
        """Perform all deployments to the requested application tiers or
           hosts
        """

        self.log.debug('Performing deployments to application tiers or hosts')

        # All is well, now do the deployment
        #   1. See if a deployment entry already exists in DB and use it,
        #      otherwise create a new one
        #   2. If deploying to tier, add an app deployment entry in DB
        #   3. Determine the appropriate hosts to deploy the application
        #   4. Do the deploy to the hosts
        dep_id = None
        pkg_deps = deploy.find_deployment_by_pkgid(pkg_id)

        if pkg_deps:
            self.log.debug(5, 'Found existing deployment')

            last_pkg_dep = pkg_deps[0]
            self.log.debug(5, 'Package deployment is: %r', last_pkg_dep)

            if last_pkg_dep.dep_type == 'deploy':
                dep_id = last_pkg_dep.id
                self.log.debug(5, 'Deployment ID is: %s', dep_id)

        if dep_id is None:
            self.log.debug(5, 'Creating new deployment')

            pkg_dep = deploy.add_deployment(pkg_id, params['user'], 'deploy')
            dep_id = pkg_dep.id
            self.log.debug(5, 'Deployment ID is: %s', dep_id)

        self.deploy_to_hosts_or_tiers(params, dep_id, app_host_map,
                                      app_dep_map)


    @tds.utils.debug
    def perform_invalidations(self, app_dep_map):
        """Perform all invalidations to the requested application tiers"""

        self.log.debug('Performing invalidations to application tiers')

        for app_id, dep_info in app_dep_map.iteritems():
            app_dep, app_type, dep_type, pkg = dep_info
            self.log.debug(5, 'Application deployment is: %r', app_dep)
            self.log.debug(5, 'Application type is: %s', app_type)
            self.log.debug(5, 'Deployment type is: %s', dep_type)
            self.log.debug(5, 'Package is: %r', pkg)

            app_dep.status = 'invalidated'


    @tds.utils.debug
    def perform_redeployments(self, params, dep_id, app_host_map,
                              app_dep_map):
        """Perform all redeployments to the requested application tiers or
           hosts
        """

        self.log.debug('Performing redeployments to application tiers or '
                       'hosts')

        self.deploy_to_hosts_or_tiers(params, dep_id, app_host_map,
                                      app_dep_map, redeploy=True)


    @tds.utils.debug
    def perform_restarts(self, params, dep_id, app_host_map, app_dep_map):
        """Perform all restarts to the requested application tiers or hosts"""

        self.log.debug('Performing restart to application tiers or hosts')

        self.restart_hosts_or_tiers(params, dep_id, app_host_map, app_dep_map)


    @tds.utils.debug
    def perform_rollbacks(self, params, app_pkg_map, app_host_map,
                          app_dep_map):
        """Perform all rollbacks to the requested application tiers
           or hosts
        """

        self.log.debug('Performing rollbacks to application tiers or hosts')

        # Since a roll back could end up at different versions for
        # each application tier, must do each tier (or host(s) in
        # tier) on its own
        for app_id, pkg_id in app_pkg_map.iteritems():
            app_dep, app_type, dep_type, pkg = app_dep_map[app_id]
            self.log.debug(5, 'Application deployment is: %r', app_dep)
            self.log.debug(5, 'Application type is: %s', app_type)
            self.log.debug(5, 'Deployment type is: %s', dep_type)
            self.log.debug(5, 'Package is: %r', pkg)

            app_id = app_dep.app_id
            self.log.debug(5, 'Application ID is: %s', app_id)

            if app_host_map is None or not app_host_map.get(app_id, None):
                self.log.debug(5, 'Creating new deployment')

                pkg_dep = deploy.add_deployment(pkg_id, params['user'],
                                                'deploy')
                dep_id = pkg_dep.id
                self.log.debug(5, 'Deployment ID is: %s', dep_id)
            else:
                # Reset app deployment to 'inprogress' (if tier rollback)
                # or 'incomplete' (if host rollback), will require
                # revalidation
                if params.get('hosts', None):
                    app_dep.status = 'incomplete'
                else:
                    app_dep.status = 'inprogress'

                Session.commit()

                dep_id = app_dep.deployment_id

            if app_host_map is None:
                single_app_host_map = None
            else:
                single_app_host_map = { app_id : app_host_map[app_id] }

            single_app_dep_map = { app_id : app_dep_map[app_id] }

            self.deploy_to_hosts_or_tiers(params, dep_id, single_app_host_map,
                                          single_app_dep_map)


    @tds.utils.debug
    def perform_validations(self, params, app_dep_map):
        """Perform all validations to the requested application tiers"""

        self.log.debug('Performing validations to application tiers')

        for app_id, dep_info in app_dep_map.iteritems():
            app_dep, app_type, dep_type, pkg = dep_info
            self.log.debug(5, 'Application deployment is: %r', app_dep)
            self.log.debug(5, 'Application type is: %s', app_type)
            self.log.debug(5, 'Deployment type is: %s', dep_type)
            self.log.debug(5, 'Package is: %r', pkg)

            # Commit to DB immediately
            app_dep.status = 'validated'
            Session.commit()

            self.log.debug(5, 'Committed database (nested) change')

            self.log.debug(5, 'Clearing host deployments for application '
                           'tier')
            deploy.delete_host_deployments(params['project'], app_dep.app_id,
                                           self.envs[params['environment']])


    @tds.utils.debug
    def process_mco_command(self, mco_cmd, retry):
        """Run a given MCollective 'mco' command"""

        self.log.debug('Running MCollective command')
        self.log.debug(5, 'Command is: %s' % ' '.join(mco_cmd))

        proc = subprocess.Popen(mco_cmd, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()

        if proc.returncode:
            return (False, 'The mco process failed to run successfully, '
                           'return code is %s' % proc.returncode)

        mc_output = None
        summary = None

        # Extract the JSON output and summary line
        for line in stdout.split('\n'):
            if line == '':
                continue

            if line.startswith('{'):
                mc_output = json.loads(line)

            if line.startswith('Finished'):
                summary = line.strip()

        # Ensure valid response and extract information
        if mc_output is None or summary is None:
            return (False, 'No output or summary information returned '
                           'from mco process')

        self.log.debug(summary)
        m = re.search(r'processing (\d+) / (\d+) ', summary)

        if m is None:
            return (False, 'Error parsing summary line.')

        # Virtual hosts in dev tend to time out unpredictably, probably
        # because vmware is slow to respond when the hosts are not
        # active. Subsequent retries after a timeout work better.
        if m.group(2) == '0' and retry > 0:
            self.log.debug('Discovery failure, trying again.')
            return self.process_mco_command(mco_cmd, retry-1)

        for host, hostinfo in mc_output.iteritems():
            if hostinfo['exitcode'] != 0:
                return (False, hostinfo['stderr'].strip())
            else:
                return (True, 'Deploy successful')

        return (False, 'Unknown/unparseable mcollective output: %s' %
                stdout)


    @tds.utils.debug
    def restart_host(self, dep_host, app, retry=4):
        """Restart application on a given host"""

        self.log.debug('Restarting application on host %r', dep_host)

        mco_cmd = [ '/usr/bin/mco', 'tds', '--discovery-timeout', '4',
                    '--timeout', '60', '-W', 'hostname=%s' % dep_host,
                    app, 'restart' ]

        return self.process_mco_command(mco_cmd, retry)


    @tds.utils.debug
    def restart_hosts(self, params, dep_hosts, dep_id):
        """Restart application on a given set of hosts"""

        self.log.debug('Restarting application on given hosts')

        failed_hosts = []

        for dep_host in sorted(dep_hosts, key=lambda host: host.hostname):
            self.log.debug(5, 'Hostname is: %s', dep_host.hostname)

            pkg = deploy.find_app_by_depid(dep_id)
            app = pkg.pkg_name
            self.log.debug(5, 'Application is: %s', app)

            success, info = self.restart_host(dep_host.hostname, app)

            if not success:
                self.log.debug(5, 'Failed to restart application on host %r',
                               dep_host.hostname)
                failed_hosts.append((dep_host.hostname, info))

            if params['delay']:
                self.log.debug(5, 'Sleeping for %d seconds...',
                               params['delay'])
                time.sleep(params['delay'])

        # If any hosts failed, show failure information for each
        if failed_hosts:
            self.log.info('Some hosts had failures:\n')

            for failed_host, reason in failed_hosts:
                self.log.info('-----')
                self.log.info('Hostname: %s', failed_host)
                self.log.info('Reason: %s', reason)


    @tds.utils.debug
    def restart_hosts_or_tiers(self, params, dep_id, app_host_map,
                               app_dep_map):
        """Restart the application on the requested hosts or application
           tiers
        """

        self.log.debug('Restarting application on requested application '
                       'tiers or hosts')

        if params.get('hosts', None):
            self.log.debug(5, 'Restarts are for hosts...')

            hostnames = []

            for hosts in app_host_map.itervalues():
                hostnames.extend(hosts)

            self.log.debug(5, 'Hostnames are: %s', ', '.join(hostnames))

            dep_hosts = [ deploy.find_host_by_hostname(x) for x in hostnames ]
            self.restart_hosts(params, dep_hosts, dep_id)
        else:
            self.log.debug(5, 'Restarts are for application tiers...')

            for app_id, dep_info in app_dep_map.iteritems():
                self.log.debug(5, 'Application ID is: %s', app_id)

                dep_hosts = deploy.find_hosts_for_app(app_id,
                                        self.envs[params['environment']])
                self.restart_hosts(params, dep_hosts, dep_id)


    @tds.utils.debug
    def send_notifications(self, params):
        """Send notifications for a given deployment"""

        self.log.debug('Sending notifications for given deployment')

        msg_subject, msg_text = self.create_notifications(params)
        notification = tds.notifications.Notifications(params['project'],
                                                       params['user'],
                                                       params['apptypes'])
        notification.send_notifications(msg_subject, msg_text)


    @tds.utils.debug
    def show_app_deployments(self, project, app_versions, env):
        """Show information for current deployment for a given application
           tier (or tiers)
        """

        self.log.debug('Showing information for current deployments '
                       'for application tiers')

        if not app_versions:
            self.log.info('No deployments to tiers for this application '
                          '(for possible given version) yet')
            self.log.info('in %s environment\n', env)
            return

        for app_type, version, revision in app_versions:
            self.log.info('Deployment of %s to %s tier in %s environment:',
                          project, app_type, env)
            self.log.info('==========\n')

            app_dep = deploy.list_app_deployment_info(project, env, app_type,
                                                      version, revision)

            dep, app_dep, pkg = app_dep

            self.log.info('Version: %s-%s', pkg.version, pkg.revision)
            self.log.info('Declared: %s', dep.declared)
            self.log.info('Declaring user: %s', dep.user)
            self.log.info('Realized: %s', app_dep.realized)
            self.log.info('Realizing user: %s', app_dep.user)
            self.log.info('App type: %s', app_type)
            self.log.info('Environment: %s', app_dep.environment)
            self.log.info('Deploy state: %s', dep.dep_type)
            self.log.info('Install state: %s', app_dep.status)
            self.log.info('')


    @tds.utils.debug
    def show_host_deployments(self, project, version, revision, apptypes,
                              env):
        """Show information for current deployment for a given host
           (or hosts)
        """

        self.log.debug('Showing information for current deployments '
                       'for hosts')

        host_deps = deploy.list_host_deployment_info(project, env,
                                                     version=version,
                                                     revision=revision,
                                                     apptypes=apptypes)

        if not host_deps:
            self.log.info('No deployments to hosts for this application '
                          '(for possible given version)')
            self.log.info('in %s environment\n', env)
        else:
            self.log.info('Deployments of %s to hosts in %s environment:',
                          project, env)
            self.log.info('==========\n')

            for dep, host_dep, hostname, pkg in host_deps:
                self.log.info('Version: %s-%s', pkg.version, pkg.revision)
                self.log.info('Declared: %s', dep.declared)
                self.log.info('Declaring user: %s', dep.user)
                self.log.info('Realized: %s', host_dep.realized)
                self.log.info('Realizing user: %s', host_dep.user)
                self.log.info('Hostname: %s', hostname)
                self.log.info('Deploy state: %s', dep.dep_type)
                self.log.info('Install state: %s', host_dep.status)
                self.log.info('')


    @tds.utils.debug
    def verify_hosts(self, hosts, app_ids, environment):
        """Verify given hosts are in the correct environment and of the
           correct app IDs
        """

        self.log.debug('Verifying hosts are in the correct environment '
                       'and of a correct application type')

        valid_hostnames = {}
        app_id_hosts_mapping = {}

        for app_id in app_ids:
            self.log.debug(5, 'Application ID is: %s', app_id)

            try:
                hostnames = [ x.hostname for x in
                              deploy.find_hosts_for_app(app_id, environment) ]
                self.log.debug(5, 'Hostnames for application ID are: %s',
                               ', '.join(hostnames))

                valid_hostnames[app_id] = hostnames
            except DeployException, e:
                # Currently we should NOT fail on this; it will
                # be caught when checking the hosts involved
                self.log.warning(e)

        bad_hosts = []

        for hostname in hosts:
            self.log.debug(5, 'Hostname is: %s', hostname)

            for app_id in valid_hostnames.iterkeys():
                self.log.debug(5, 'Application ID for hostname is: %s',
                               app_id)

                if hostname in valid_hostnames[app_id]:
                    self.log.debug(5, 'Hostname %r is valid', hostname)
                    host_map_list = \
                        app_id_hosts_mapping.setdefault(app_id, [])
                    host_map_list.append(hostname)
                    break
            else:
                self.log.debug(5, 'Hostname %r was invalid', hostname)
                bad_hosts.append(hostname)

        if bad_hosts:
            self.log.info('The following hosts are in the wrong environment '
                          'or do not belong to a matching app type: %s',
                          ', '.join(bad_hosts))
            sys.exit(1)

        self.log.debug(5, 'App ID/hosts map is: %r', app_id_hosts_mapping)

        return app_id_hosts_mapping


    @tds.utils.debug
    def verify_package(self, params, hostonly=False):
        """Ensure requested package is valid (exists in the software
           repository)
        """

        self.log.debug('Verifying requested package')

        app_ids = self.get_app_types(params)
        pkg_id = self.get_package_id(params, app_ids, hostonly)

        if params.get('hosts', None):
            self.log.debug(5, 'Verification is for hosts...')

            app_host_map = self.verify_hosts(params['hosts'], app_ids,
                                             self.envs[params['environment']])
            self.log.debug(5, 'Application/host map is: %r', app_host_map)

            return (pkg_id, app_host_map)
        else:
            self.log.debug(5, 'Verification is for application tiers...')
            self.log.debug(5, 'Applications IDs are: %s',
                           ', '.join([ str(x) for x in app_ids ]))

            return (pkg_id, app_ids)


    @tds.utils.debug
    def verify_project_type(self, project):
        """Ensure correct command is being used for given project"""

        self.log.debug('Verifying project type is correct')

        try:
            # Tuple of one returned, just get the value
            project_type = repo.find_project_type(project)[0]
            self.log.debug(5, 'Project type is: %s', project_type)
        except RepoException, e:
            self.log.error(e)
            sys.exit(1)

        if project_type not in self.valid_project_types:
            raise WrongProjectTypeError('Project "%s" is not valid for '
                                        'this command' % project)

        return project_type


    @tds.utils.debug
    @catch_exceptions
    def add_apptype(self, params):
        """Add a specific application type to the given project"""

        self.log.debug('Adding application type for project')

        tds.authorize.verify_access(params['user_level'], 'admin')

        self.proj_type = self.verify_project_type(params['project'])

        try:
            app = repo.find_app_location(params['project'])
            # Transitional code for refactoring
            project_new = repo.find_project(params['project'])
            pkg_def = package.find_package_definition(project_new.id)

            repo.add_app_packages_mapping(app, project_new, pkg_def,
                                          [params['apptype']])
        except RepoException, e:
            self.log.error(e)
            return

        Session.commit()
        self.log.debug('Committed database changes')


    @tds.utils.debug
    @catch_exceptions
    def delete_apptype(self, params):
        """Delete a specific application type from the given project"""

        self.log.debug('Removing application type for project')

        tds.authorize.verify_access(params['user_level'], 'admin')

        self.proj_type = self.verify_project_type(params['project'])

        try:
            app = repo.find_app_location(params['project'])
            repo.delete_app_packages_mapping(app, [params['apptype']])
        except RepoException, e:
            self.log.error(e)
            return

        Session.commit()
        self.log.debug('Committed database changes')


    @tds.utils.debug
    @catch_exceptions
    def invalidate(self, params):
        """Invalidate a given version of a given project"""

        self.log.debug('Invalidating for given project')

        # Not a deployment
        params['deployment'] = False

        tds.authorize.verify_access(params['user_level'],
                                    params['environment'])

        self.proj_type = self.verify_project_type(params['project'])
        self.ensure_explicit_destinations(params)

        pkg_id, app_ids, app_host_map = self.get_app_info(params)
        app_dep_map = self.find_app_deployments(pkg_id, app_ids, params)

        if not len(filter(None, app_dep_map.itervalues())):
            self.log.info('No deployments to invalidate for application %r '
                          'with version %r in %s environment',
                          params['project'], params['version'],
                          self.envs[params['environment']])
            return

        app_dep_map = self.determine_invalidations(params, app_ids,
                                                   app_dep_map)
        self.perform_invalidations(app_dep_map)

        Session.commit()
        self.log.debug('Committed database changes')


    @tds.utils.debug
    @catch_exceptions
    def show(self, params):
        """Show deployment information for a given project"""

        self.log.debug('Showing deployment information for given project')

        tds.authorize.verify_access(params['user_level'], 'dev')

        self.proj_type = self.verify_project_type(params['project'])

        if params['version'] is None:
            app_versions = deploy.find_latest_deployed_version(
                                  params['project'],
                                  self.envs[params['environment']],
                                  apptypes=params['apptypes'], apptier=True)
        else:
            app_versions = deploy.find_deployed_version(params['project'],
                                       self.envs[params['environment']],
                                       version=params['version'],
                                       apptypes=params['apptypes'],
                                       apptier=True)

        self.log.debug(5, 'Application versions are: %r', app_versions)

        self.show_app_deployments(params['project'], app_versions,
                                  self.envs[params['environment']])
        # Revision is hardcoded to '1' for now
        self.show_host_deployments(params['project'], params['version'], '1',
                                   params['apptypes'],
                                   self.envs[params['environment']])


    @tds.utils.debug
    @catch_exceptions
    def validate(self, params):
        """Validate a given version of a given project"""

        self.log.debug('Validating for given project')

        # Not a deployment
        params['deployment'] = False

        tds.authorize.verify_access(params['user_level'],
                                    params['environment'])

        self.proj_type = self.verify_project_type(params['project'])
        self.ensure_explicit_destinations(params)

        pkg_id, app_ids, app_host_map = self.get_app_info(params)
        app_dep_map = self.find_app_deployments(pkg_id, app_ids, params)

        if not len(filter(None, app_dep_map.itervalues())):
            self.log.info('No deployments to validate for application %r '
                          'in %s environment', params['project'],
                          self.envs[params['environment']])
            return

        app_dep_map = self.determine_validations(params, pkg_id, app_ids,
                                                 app_dep_map)
        self.perform_validations(params, app_dep_map)

        Session.commit()
        self.log.debug('Committed database changes')


class Config(BaseDeploy):
    """Commands to manage deployments for supported config applications"""

    def __init__(self, logger):
        """Basic initialization"""

        super(Config, self).__init__(logger)
        self.valid_project_types = [ 'tagconfig', 'kafka-config' ]


    @tds.utils.debug
    def check_previous_environment(self, params, pkg_id, app_id):
        """Placeholder method as config projects don't check
           the previous environment for validation (due to
           differences in configuration information)
        """

        self.log.debug('Previous environment not required for config '
                       'projects')

        return True


    @tds.utils.debug
    @catch_exceptions
    def create(self, params):
        """Add a new config project to the system"""

        self.log.debug('Creating new config project')

        tds.authorize.verify_access(params['user_level'], 'admin')

        # Currently project type matches the project name
        if params['project'] not in self.valid_project_types:
            raise WrongProjectTypeError('Project "%s" is not valid for '
                                        'this command' % params['project'])

        try:
            self.log.debug(5, 'Adding config project to repository')

            # Project type matches project name
            repo.add_app_location(params['project'], params['buildtype'],
                                  params['pkgname'], params['project'],
                                  params['pkgpath'], params['arch'],
                                  params['buildhost'], params['env_specific'])
        except RepoException, e:
            self.log.error(e)
            return

        Session.commit()
        self.log.debug('Committed database changes')


    @tds.utils.debug
    @catch_exceptions
    def delete(self, params):
        """Remove a config project from the system"""

        self.log.debug('Removing given config project')

        tds.authorize.verify_access(params['user_level'], 'admin')

        self.proj_type = self.verify_project_type(params['project'])

        try:
            repo.delete_app_location(params['project'])
        except RepoException, e:
            self.log.error(e)
            return

        Session.commit()
        self.log.debug('Committed database changes')


    @tds.utils.debug
    @catch_exceptions
    def push(self, params):
        """Push given version of given config project to requested application
           tiers or hosts
        """

        self.log.debug('Pushing config project')

        tds.authorize.verify_access(params['user_level'],
                                    params['environment'])

        self.proj_type = self.verify_project_type(params['project'])
        self.ensure_explicit_destinations(params)

        if not self.ensure_newer_versions(params):
            return

        pkg_id, app_ids, app_host_map = self.get_app_info(params)

        try:
            app_dep_map = self.find_app_deployments(pkg_id, app_ids, params)
        except NoCurrentDeploymentError, e:
            pass

        app_host_map, app_dep_map = \
            self.determine_new_deployments(params, pkg_id, app_ids,
                                           app_host_map, app_dep_map)
        self.send_notifications(params)
        self.perform_deployments(params, pkg_id, app_host_map, app_dep_map)

        Session.commit()
        self.log.debug('Committed database changes')


    @tds.utils.debug
    @catch_exceptions
    def repush(self, params):
        """Repush given config project to requested application tiers or
           hosts
        """

        self.log.debug('Repushing config project')

        tds.authorize.verify_access(params['user_level'],
                                    params['environment'])

        self.proj_type = self.verify_project_type(params['project'])
        self.ensure_explicit_destinations(params)

        pkg_id, app_ids, app_host_map = self.get_app_info(params,
                                                          hostonly=True)
        app_dep_map = self.find_app_deployments(pkg_id, app_ids, params)

        if not len(filter(None, app_dep_map.itervalues())):
            self.log.info('Nothing to repush for configuration %r in %s '
                          'environment', params['project'],
                          self.envs[params['environment']])
            return

        dep_id = self.determine_redeployments(pkg_id)
        self.send_notifications(params)
        self.perform_redeployments(params, dep_id, app_host_map, app_dep_map)

        Session.commit()
        self.log.debug('Committed database changes')


    @tds.utils.debug
    @catch_exceptions
    def revert(self, params):
        """Revert to the previous validated deployed version of given config
           project on requested application tiers or hosts
        """

        self.log.debug('Reverting config project')

        tds.authorize.verify_access(params['user_level'],
                                    params['environment'])

        self.proj_type = self.verify_project_type(params['project'])
        self.ensure_explicit_destinations(params)

        pkg_id, app_ids, app_host_map = self.get_app_info(params)
        app_dep_map = self.find_app_deployments(pkg_id, app_ids, params)

        if not len(filter(None, app_dep_map.itervalues())):
            self.log.info('Nothing to revert for configuration %r in %s '
                          'environment', params['project'],
                          self.envs[params['environment']])
            return

        # Save verison of application/deployment map for invalidation
        # at the end of the run
        self.log.debug(5, 'Saving current application/deployment map')
        orig_app_dep_map = app_dep_map

        app_pkg_map, app_host_map, app_dep_map = \
            self.determine_rollbacks(params, app_ids, app_host_map,
                                     app_dep_map)
        self.send_notifications(params)
        self.perform_rollbacks(params, app_pkg_map, app_host_map, app_dep_map)

        if not params.get('hosts', None):
            # Now perform invalidations, commit immediately follows
            # Note this is only done for tiers
            self.perform_invalidations(orig_app_dep_map)

        Session.commit()
        self.log.debug('Committed database changes')


class Deploy(BaseDeploy):
    """Commands to manage deployments for supported applications"""

    def __init__(self, logger):
        """Basic initialization"""

        super(Deploy, self).__init__(logger)
        self.valid_project_types = [ 'application' ]


    @tds.utils.debug
    def check_previous_environment(self, params, pkg_id, app_id):
        """Ensure deployment for previous environment for given package
           and apptier was validated; this is only relevant for staging
           and production environments
        """

        self.log.debug('Checking for validation in previous environment')

        if params['environment'] != 'dev':
            prev_env = self.get_previous_environment(params['environment'])
            self.log.debug(5, 'Previous environment is: %s', prev_env)

            prev_deps = deploy.find_app_deployment(pkg_id, [ app_id ],
                                                   self.envs[prev_env])
            # There might be no deployment available; otherwise
            # there should only be one deployment here
            if not prev_deps:
                self.log.info('Application %r with version %r never '
                              'deployed to previous environment (%s) '
                              'for current apptype', params['project'],
                              params['version'], prev_env)
                return False

            prev_app_dep, prev_app_type, prev_dep_type, \
                prev_pkg = prev_deps[0]
            self.log.debug(5, 'Previous application deployment is: %r',
                           prev_app_dep)
            self.log.debug(5, 'Previous application type is: %s',
                           prev_app_type)
            self.log.debug(5, 'Previous deployment type is: %s',
                           prev_dep_type)
            self.log.debug(5, 'Previous package is: %r', prev_pkg)

            if (prev_dep_type != 'deploy' or
                prev_app_dep.status != 'validated'):
                self.log.info('Application %r with version %r not fully '
                              'deployed or validated to previous environment '
                              '(%s) for apptype %r', params['project'],
                              params['version'], prev_env, prev_app_type)
                return False

        self.log.debug(5, 'In development environment, nothing to check')

        return True


    @tds.utils.debug
    @catch_exceptions
    def force_production(self, params):
        """Allow deployment to production of given project without the
           previous environment check
        """

        self.log.debug('Deploying project to production (without environment '
                       'check)')

        tds.authorize.verify_access(params['user_level'], 'admin')

        raise NotImplementedError('This subcommand is currently not '
                                  'implemented')


    @tds.utils.debug
    @catch_exceptions
    def force_staging(self, params):
        """Allow deployment to staging of given project without the
           previous environment check
        """

        self.log.debug('Deploying project to staging (without environment '
                       'check)')

        tds.authorize.verify_access(params['user_level'], 'admin')

        raise NotImplementedError('This subcommand is currently not '
                                  'implemented')


    @tds.utils.debug
    @catch_exceptions
    def promote(self, params):
        """Deploy given version of given project to requested application
           tiers or hosts
        """

        self.log.debug('Deploying project')

        tds.authorize.verify_access(params['user_level'],
                                    params['environment'])

        self.proj_type = self.verify_project_type(params['project'])
        self.ensure_explicit_destinations(params)

        if not self.ensure_newer_versions(params):
            return

        pkg_id, app_ids, app_host_map = self.get_app_info(params)
        app_dep_map = self.find_app_deployments(pkg_id, app_ids, params)
        app_host_map, app_dep_map = \
            self.determine_new_deployments(params, pkg_id, app_ids,
                                           app_host_map, app_dep_map)
        self.send_notifications(params)
        self.perform_deployments(params, pkg_id, app_host_map, app_dep_map)

        Session.commit()
        self.log.debug('Committed database changes')


    @tds.utils.debug
    @catch_exceptions
    def redeploy(self, params):
        """Redeploy given project to requested application tiers or hosts"""

        self.log.debug('Redeploying project')

        tds.authorize.verify_access(params['user_level'],
                                    params['environment'])

        self.proj_type = self.verify_project_type(params['project'])
        self.ensure_explicit_destinations(params)

        pkg_id, app_ids, app_host_map = self.get_app_info(params,
                                                          hostonly=True)
        app_dep_map = self.find_app_deployments(pkg_id, app_ids, params)

        if not len(filter(None, app_dep_map.itervalues())):
            self.log.info('Nothing to redeploy for application %r in %s '
                          'environment', params['project'],
                          self.envs[params['environment']])
            return

        dep_id = self.determine_redeployments(pkg_id)
        self.send_notifications(params)
        self.perform_redeployments(params, dep_id, app_host_map, app_dep_map)

        Session.commit()
        self.log.debug('Committed database changes')


    @tds.utils.debug
    @catch_exceptions
    def restart(self, params):
        """Restart given project on requested application tiers or hosts"""

        self.log.debug('Restarting application for project')

        # Not a deployment
        params['deployment'] = False

        tds.authorize.verify_access(params['user_level'],
                                    params['environment'])

        self.proj_type = self.verify_project_type(params['project'])
        self.ensure_explicit_destinations(params)

        pkg_id, app_ids, app_host_map = self.get_app_info(params)
        app_dep_map = self.find_app_deployments(pkg_id, app_ids, params)

        if not len(filter(None, app_dep_map.itervalues())):
            self.log.info('Nothing to restart for application %r in %s '
                          'environment', params['project'],
                          self.envs[params['environment']])
            return

        dep_id = self.determine_restarts(pkg_id)
        self.perform_restarts(params, dep_id, app_host_map, app_dep_map)


    @tds.utils.debug
    @catch_exceptions
    def rollback(self, params):
        """Rollback to the previous validated deployed version of given
           project on requested application tiers or hosts
        """

        self.log.debug('Rolling back project')

        tds.authorize.verify_access(params['user_level'],
                                    params['environment'])

        self.proj_type = self.verify_project_type(params['project'])
        self.ensure_explicit_destinations(params)

        pkg_id, app_ids, app_host_map = self.get_app_info(params)
        app_dep_map = self.find_app_deployments(pkg_id, app_ids, params)

        if not len(filter(None, app_dep_map.itervalues())):
            self.log.info('Nothing to roll back for application %r in %s '
                          'environment', params['project'],
                          self.envs[params['environment']])
            return

        # Save verison of application/deployment map for invalidation
        # at the end of the run
        self.log.debug(5, 'Saving current application/deployment map')
        orig_app_dep_map = app_dep_map

        app_pkg_map, app_host_map, app_dep_map = \
            self.determine_rollbacks(params, app_ids, app_host_map,
                                     app_dep_map)
        self.send_notifications(params)
        self.perform_rollbacks(params, app_pkg_map, app_host_map, app_dep_map)

        if not params.get('hosts', None):
            # Now perform invalidations, commit immediately follows
            # Note this is only done for tiers
            self.perform_invalidations(orig_app_dep_map)

        Session.commit()
        self.log.debug('Committed database changes')
