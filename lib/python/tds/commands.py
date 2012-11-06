import errno
import os
import os.path
import re
import signal
import socket
import subprocess
import sys
import time

import json

from tagopsdb.database.meta import Session
from tagopsdb.exceptions import RepoException, PackageException, \
                                DeployException, NotImplementedException

import tagopsdb.deploy.repo as repo
import tagopsdb.deploy.package as package
import tagopsdb.deploy.deploy as deploy

import tds.authorize
import tds.notifications

from tds.exceptions import NotImplementedError, WrongEnvironmentError, \
                           WrongProjectTypeError


def catch_exceptions(meth):
    """Catch common database library exceptions"""

    def wrapped(*args, **kwargs):
        try:
            meth(*args, **kwargs)
        except NotImplementedException, e:
            raise NotImplementedError(e)

    return wrapped


class Repository(object):
    """ """

    def __init__(self):
        """ """

        pass


    @catch_exceptions
    def add(self, args):
        """ """

        tds.authorize.verify_access(args.user_level, 'admin')

        try:
            # For now, project_type is 'application'
            args.projecttype = 'application'
            loc_id = repo.add_app_location(args.projecttype, args.buildtype,
                                           args.pkgname, args.project,
                                           args.pkgpath, args.buildhost,
                                           args.env_specific)
            repo.add_app_packages_mapping(loc_id, args.apptypes)
        except RepoException, e:
            print e
            return

        if args.config:
            try:
                config = repo.list_app_location(args.config)
                repo.add_app_packages_mapping(config.pkgLocationID,
                                              args.apptypes)
            except RepoException, e:
                print e
                return

        Session.commit()


    @catch_exceptions
    def delete(self, args):
        """ """

        tds.authorize.verify_access(args.user_level, 'admin')

        try:
            repo.delete_app_location(args.project)
        except RepoException, e:
            print e
            return

        Session.commit()


    @catch_exceptions
    def list(self, args):
        """ """

        tds.authorize.verify_access(args.user_level, 'dev')

        for app in repo.list_all_app_locations():
            print 'Project: %s' % app.app_name
            print 'Project type: %s' % app.project_type
            print 'Package type: %s' % app.pkg_type
            print 'Package name: %s' % app.pkg_name
            print 'Path: %s' % app.path
            print 'Build host: %s' % app.build_host

            app_defs = repo.find_app_packages_mapping(app.app_name)
            app_types = [ x.appType for x in app_defs ]
            print 'App types: %s' % ', '.join(app_types)

            if app.environment:
                is_env = 'Yes'
            else:
                is_env = 'No'

            print 'Environment specific: %s' % is_env
            print ''


class Package(object):
    """ """

    def __init__(self):
        """ """

        self.host = socket.gethostname()


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
                with open(path) as fh:
                    time.sleep(0.5)
            except IOError, e:
                if e.errno == errno.ENOENT:
                    break


    @catch_exceptions
    def add(self, args):
        """ """

        tds.authorize.verify_access(args.user_level, 'dev')

        try:
            # The real 'revision' is hardcoded to 1 for now
            # This needs to be changed at some point
            package.add_package(args.project, args.version, '1', args.user)
        except PackageException, e:
            print e
            return

        # Get repo information for package
        app = repo.list_app_location(args.project)

        # Verify required RPM exists and create hard link into
        # the incoming directory for the repository server to find,
        # then wait until file has been removed or timeout with
        # error (meaning repository side failed, check logs there)
        build_base = args.repo['build_base']
        incoming_dir = args.repo['incoming']
        processing_dir = args.repo['processing']

        # Revision hardcoded for now
        src_rpm = os.path.join(build_base, app.path, '%s-%s-1.noarch.rpm'
                               % (app.pkg_name, args.version))
        queued_rpm = os.path.join(incoming_dir, '%s-%s-1.noarch.rpm'
                                  % (app.pkg_name, args.version))
        process_rpm = os.path.join(processing_dir, '%s-%s-1.noarch.rpm'
                                   % (app.pkg_name, args.version))

        print 'Checking for existance of file "%s"...' % src_rpm

        if not os.path.isfile(src_rpm):
            print 'File "%s" is not found in "%s"' % (src_rpm, build_base)
            return

        try:
            print 'Build host "%s" built RPM successfully' % app.build_host
            print 'Linking RPM into incoming directory...'
            os.link(src_rpm, queued_rpm)
        except Exception, e:   # Really need to narrow the exception down
            print e
            return

        print 'RPM successfully linked, waiting for repository server'
        print '  to update deploy repo...'

        signal.signal(signal.SIGALRM, self.processing_handler)
        signal.alarm(60)

        self.wait_for_file_removal(queued_rpm)
        self.wait_for_file_removal(process_rpm)

        signal.alarm(0)

        Session.commit()

        print 'Added package for project "%s", version %s' \
              % (args.project, args.version)


    @catch_exceptions
    def delete(self,args):
        """ """

        tds.authorize.verify_access(args.user_level, 'dev')

        try:
            # The real 'revision' is hardcoded to 1 for now
            # This needs to be changed at some point
            package.delete_package(args.project, args.version, '1')
        except PackageException, e:
            print e
            return

        Session.commit()


    @catch_exceptions
    def list(self, args):
        """ """

        tds.authorize.verify_access(args.user_level, 'dev')

        for pkg in package.list_packages():
            print 'Project: %s' % pkg.pkg_name
            print 'Version: %s' % pkg.version
            print 'Revision: %s' % pkg.revision
            print ''


class BaseDeploy(object):
    """ """

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


    def __init__(self):
        """ """

        self.valid_project_types = None


    def check_tier_state(self, args, pkg_id, app_dep):
        """Ensure state of tier (from given app deployment) is consistent
           with state and deployment package versions
        """

        apptype_hosts = deploy.find_hosts_for_app(app_dep.AppID,
                                              self.envs[args.environment])
        apptype_hostnames = [ x.hostname for x in apptype_hosts ]

        dep_hosts = deploy.find_host_deployments_by_project(args.project,
                                                    apptype_hostnames)
        dep_hostnames = [ x.hostname for x in dep_hosts ]

        missing_deps = list(set(apptype_hostnames) - set(dep_hostnames))
        version_diffs = [ x.hostname for x in dep_hosts
                          if int(x.version) != args.version ]

        not_ok_hosts = deploy.find_host_deployments_not_ok(pkg_id,
                              app_dep.AppID, self.envs[args.environment])
        not_ok_hostnames = [ x.hostname for x in not_ok_hosts ]

        if (missing_deps or version_diffs or not_ok_hosts):
            return ('failed', missing_deps, version_diffs, not_ok_hostnames)
        else:
            return ('ok', [], [], [])


    def create_notifications(self, args):
        """Create subject and message for a notification"""

        dep_type = self.dep_types[args.subcommand_name]

        if getattr(args, 'hosts', None):
            dest_type = 'hosts'
            destinations = ', '.join(args.hosts)
        elif getattr(args, 'apptypes', None):
            dest_type = 'app tier(s)'
            destinations = ', '.join(args.apptypes)
        else:
            dest_type = 'app tier(s)'
            destinations = ', '.join([ x.appType for x in
                           repo.find_app_packages_mapping(args.project) ])

        msg_subject = '%s of %s on %s %s in %s' \
                      % (dep_type, args.project, dest_type, destinations,
                         self.envs[args.environment])
        msg_text = '%s performed a "tds %s %s" for the following %s ' \
                   'in %s:\n    %s' \
                   % (args.user, args.command_name, args.subcommand_name,
                      dest_type, self.envs[args.environment], destinations)

        return msg_subject, msg_text


    def deploy_to_host(self, dep_host, app, version, retry=4):
        """Deploy specified package to a given host"""

        mco_cmd = [ '/usr/bin/mco', 'tds', '--discovery-timeout', '4',
                    '--timeout', '60', '-W', 'hostname=%s' % dep_host,
                    app, version ]

        return self.process_mco_command(mco_cmd, retry)


    def deploy_to_hosts(self, args, dep_hosts, dep_id, redeploy=False):
        """Perform deployment on given set of hosts (only doing those
           that previously failed with a redeploy)
        """

        failed_hosts = []

        for dep_host in dep_hosts:
            pkg = deploy.find_app_by_depid(dep_id)
            app, version = pkg.pkg_name, pkg.version

            host_dep = deploy.find_host_deployment_by_depid(dep_id,
                                                            dep_host.hostname)

            if redeploy and host_dep and host_dep.status != 'ok':
                success, info = self.deploy_to_host(dep_host.hostname, app,
                                                    version)

                if success:
                    # Commit to DB immediately
                    Session.begin_nested()
                    host_dep.status = 'ok'
                    Session.commit()
                else:
                    failed_hosts.append((dep_host.hostname, info))
            else:
                if host_dep and host_dep.status == 'ok':
                    print 'Host "%s" already has version "%s" of ' \
                          'application "%s" successfully deployed, skipping' \
                          % (dep_host.hostname, version, app)
                    continue

                # Clear out any old deployments for this host
                deploy.delete_host_deployment(dep_host.hostname, args.project)
                host_dep = deploy.add_host_deployment(dep_id, dep_host.HostID,
                                                      args.user, 'incomplete')
                success, info = self.deploy_to_host(dep_host.hostname, app,
                                                    version)

                if success:
                    # Commit to DB immediately
                    Session.begin_nested()
                    host_dep.status = 'ok'
                    Session.commit()
                else:
                    # Commit to DB immediately
                    Session.begin_nested()
                    host_dep.status = 'failed'
                    Session.commit()

                    failed_hosts.append((dep_host.hostname, info))

        # If any hosts failed, show failure information for each
        if failed_hosts:
            print 'Some hosts had failures:\n'

            for failed_host, reason in failed_hosts:
                print '-----'
                print 'Hostname: %s' % failed_host
                print 'Reason: %s' % reason


    def deploy_to_hosts_or_tiers(self, args, dep_id, app_host_map,
                                 app_dep_map, redeploy=False):
        """Do the deployment to the requested hosts or application tiers"""

        if getattr(args, 'hosts', None):
            hostnames = []

            for hosts in app_host_map.itervalues():
                hostnames.extend(hosts)

            dep_hosts = [ deploy.find_host_by_hostname(x) for x in hostnames ]
            self.deploy_to_hosts(args, dep_hosts, dep_id, redeploy=redeploy)
        else:
            for app_id, dep_info in app_dep_map.iteritems():
                if redeploy:
                    app_dep, app_type, dep_type, pkg = dep_info

                    # Don't redeploy to a validated tier
                    if app_dep.status == 'validated':
                        print 'Application "%s" with version "%s" already ' \
                              'validated on app type %s"' \
                              % (args.project, pkg.version, app_type)
                        continue
                else:
                    deploy.add_app_deployment(dep_id, app_id, args.user,
                                              'incomplete',
                                              self.envs[args.environment])

                dep_hosts = deploy.find_hosts_for_app(app_id,
                                              self.envs[args.environment])
                self.deploy_to_hosts(args, dep_hosts, dep_id,
                                     redeploy=redeploy)


    def determine_invalidations(self, args, app_ids, app_dep_map):
        """ """

        curr_deps = deploy.find_latest_deployed_version(args.project,
                                                self.envs[args.environment],
                                                apptier=True)
        curr_dep_versions = {}

        for app_type, version, revision in curr_deps:
            curr_dep_versions[app_type] = int(version)

        for app_id in app_ids:
            if not app_dep_map[app_id]:
                continue

            ok = True

            app_dep, app_type, dep_type, pkg = app_dep_map[app_id]

            # Ensure version to invalidate isn't the current
            # deployment for this app type
            if curr_dep_versions.get(app_type, None) == args.version:
                print 'Unable to invalidate application "%s" with ' \
                      'version "%s" for apptype "%s" as that version ' \
                      'is currently deployed for the apptype' \
                      % (args.project, args.version, app_type)
                ok = False

            if ok:
                if app_dep.status != 'validated':
                    print 'Deployment for application "%s" with version ' \
                          '"%s" for apptype "%s" has not been validated in ' \
                          '%s environment' \
                          % (args.project, args.version, app_type,
                             self.envs[args.environment])
                    ok = False

            if not ok:
                del app_dep_map[app_id]

        return app_dep_map


    def determine_new_deployments(self, args, pkg_id, app_ids, app_host_map,
                                  app_dep_map):
        """ """

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
            ok = self.check_previous_environment(args, pkg_id, app_id)

            if ok:
                if not app_dep_map[app_id]:
                    continue

                app_dep, app_type, dep_type, pkg = app_dep_map[app_id]

                if (app_dep.status != 'invalidated' and
                    dep_type == 'deploy' and pkg.version == args.version):
                    print 'Application "%s" with version "%s" already ' \
                          'deployed to this environment (%s) for ' \
                          'apptype "%s"' \
                          % (args.project, args.version,
                             self.envs[args.environment], app_type)
                    ok = False

            if not ok:
                if getattr(args, 'hosts', None):
                    del app_host_map[app_id]
                else:
                    del app_dep_map[app_id]

        return (app_host_map, app_dep_map)


    def determine_redeployments(self, pkg_id):
        """Find the deployment entry in the database for the redeployments"""

        pkg_deps = deploy.find_deployment_by_pkgid(pkg_id)
        last_pkg_dep = pkg_deps[0]  # Guaranteed to have at least one

        return last_pkg_dep.DeploymentID


    def determine_restarts(self, pkg_id):
        """Find the deployment entry in the database for the restarts"""

        pkg_deps = deploy.find_deployment_by_pkgid(pkg_id)
        last_pkg_dep = pkg_deps[0]  # Guaranteed to have at least one

        return last_pkg_dep.DeploymentID


    def determine_rollbacks(self, args, app_ids, app_dep_map):
        """ """

        app_pkg_map = {}

        for app_id in app_ids:
            if not app_dep_map[app_id]:
                continue

            ok = True

            last_app_dep, last_pkg_id = \
                deploy.find_latest_validated_deployment(args.project, app_id,
                                             self.envs[args.environment])
            if last_pkg_id is None:
                print 'No previous deployment to roll back to for ' \
                      'application "%s" for app type "%s" in %s ' \
                      'environment' % (args.project, app_id,
                                       self.envs[args.environment])
                ok = False
            else:
                app_pkg_map[app_id] = last_pkg_id

            if not ok:
                del app_dep_map[app_id]

        return (app_pkg_map, app_dep_map)


    def determine_validations(self, args, pkg_id, app_ids, app_dep_map):
        """ """

        for app_id in app_ids:
            if not app_dep_map[app_id]:
                continue

            ok = True

            app_dep, app_type, dep_type, pkg = app_dep_map[app_id]

            if app_dep.status == 'validated':
                print 'Deployment for application "%s" for apptype "%s" ' \
                      'already validated in %s environment' \
                      % (args.project, app_type, self.envs[args.environment])
                ok = False

            if ok:
                # Ensure tier state is consistent
                result, missing, diffs, not_ok = \
                    self.check_tier_state(args, pkg_id, app_dep)

                if result != 'ok':
                    print 'Unable to validate version "%s" of application ' \
                          '"%s" due to the current issues:' \
                          % (args.version, args.project)

                    if missing:
                        print '  Hosts missing deployments of given version:'
                        print '    %s' % ', '.join(missing)

                    if diffs:
                        print '  Hosts with different versions than the ' \
                              'one being validated:'
                        print '    %s' % ', '.join(diffs)

                    if not_ok:
                        print '  Hosts not in an "ok" state:'
                        print '    %s' % ', '.join(hostnames)

                    ok = False

            if not ok:
                del app_dep_map[app_id]

        return app_dep_map


    def ensure_explicit_destinations(self, args):
        """Make sure multiple application types are explicit"""

        if not args.explicit and len(self.get_app_types(args)) > 1:
            print 'Application "%s" has multiple corresponding app types, ' \
                  'please use "--apptypes" or "--all-apptypes"' \
                  % args.project
            sys.exit(1)


    def ensure_newer_versions(self, args):
        """Ensure version being deployed is more recent than
           the currently deployed versions on requested app types
        """

        newer_versions = []
        dep_versions = deploy.find_latest_deployed_version(args.project,
                              self.envs[args.environment], apptier=True)

        for dep_app_type, dep_version, dep_revision in dep_versions:
            # Currently not using revision (always '1' at the moment)
            # 'dep_version' must be typecast to an integer as well,
            # since the DB stores it as a string - may move away from
            # integers for versions in the future, so take note here
            if args.version < int(dep_version):
                newer_versions.append(dep_app_type)

        if newer_versions:
            app_type_list = ', '.join(['"%s"' % x for x in newer_versions])
            print 'Application "%s" for app types %s have newer versions ' \
                  'deployed than the requested version "%s"' \
                  % (args.project, app_type_list, args.version)
            return False

        return True


    def find_app_deployments(self, pkg_id, app_ids, args):
        """Find all relevant application deployments for the requested
        app types and create an application/deployment mapping,
        keeping track of which app types have a current deployment
        and which don't
        """

        deps = deploy.find_app_deployment(pkg_id, app_ids,
                                          self.envs[args.environment])

        app_dep_map = {}

        for app_id in app_ids:
            app_dep_map[app_id] = None

        for app_dep, app_type, dep_type, pkg in deps:
            app_dep_map[app_dep.AppID] = (app_dep, app_type, dep_type, pkg)

        return app_dep_map


    def get_app_info(self, args, hostonly=False):
        """Verify requested package and which hosts or app tiers
        to install the package; for hosts a mapping is kept between
        them and their related app types
        """

        if getattr(args, 'hosts', None):
            try:
                pkg_id, app_host_map = self.verify_package(args,
                                                           hostonly=hostonly)
            except ValueError, e:
                print '%s for given project and hosts' % e
                sys.exit(1)

            host_deps = deploy.find_host_deployments_by_project(args.project,
                                                                args.hosts)

            for host_dep, hostname, app_id, dep_version in host_deps:
                curr_version = getattr(args, 'version', dep_version)

                if dep_version == curr_version and host_dep.status == 'ok':
                    print 'Application "%s" with version "%s" already ' \
                          'deployed to host "%s"' \
                          % (args.project, curr_version, hostname)
                    app_host_map[app_id].remove(hostname)

                    if not app_host_map[app_id]:
                        del app_host_map[app_id]

            app_ids = app_host_map.keys()
        else:
            try:
                pkg_id, app_ids = self.verify_package(args)
            except ValueError, e:
                print '%s for given project and application tiers' % e
                sys.exit(1)

            app_host_map = None   # No need for this for tiers

        return (pkg_id, app_ids, app_host_map)


    def get_app_types(self, args):
        """Determine application IDs for deployment"""

        try:
            app_ids = [ x.AppID for x
                        in repo.find_app_packages_mapping(args.project) ]
        except RepoException, e:
            print e
            sys.exit(1)

        if args.apptypes:
            try:
                app_defs = [ deploy.find_app_by_apptype(x)
                             for x in args.apptypes ]
            except DeployException, e:
                print e
                sys.exit(1)

            new_app_ids = [ x.AppID for x in app_defs ]

            if set(new_app_ids).issubset(set(app_ids)):
                app_ids = new_app_ids
            else:
                print 'One of the app types given is not a valid app type ' \
                      'for the current deployment'
                sys.exit(1)

        return app_ids


    def get_package_id(self, args, app_ids, hostonly=False):
        """Get the package ID for the current project and version
           (or most recent deployed version if none is given) for
           a given set of application types
        """

        app_types = [ deploy.find_apptype_by_appid(x) for x in app_ids ]

        if hasattr(args, 'version'):
            version = args.version
        else:
            # Must determine latest deployed version(s);
            # they must all use the same package version
            # (Tuple of app_type, version, revision returned
            #  with DB query)
            apptier = not hostonly
            last_deps = deploy.find_latest_deployed_version(args.project,
                               self.envs[args.environment], apptier=apptier)

            if hostonly:
                versions = [ x.version for x in last_deps
                             if x.AppID in app_ids ]
            else:
                versions = [ x.version for x in last_deps
                             if x.appType in app_types ]

            if not versions:
                print 'Application "%s" has no current tier/host ' \
                      'deployments to verify for the given apptypes/hosts' \
                      % args.project
                sys.exit(1)

            if not all(x == versions[0] for x in versions):
                raise ValueError('Multiple versions not allowed')

            version = versions[0]

        try:
            # Revision hardcoded to '1' for now
            pkg = package.find_package(args.project, version, '1')
            if not pkg:
                print 'Application "%s" with version "%s" not ' \
                      'available in the repository.' % (args.project, version)
                sys.exit(1)
        except PackageException, e:
            print e
            sys.exit(1)

        return pkg.PackageID


    def get_previous_environment(self, curr_env):
        """Find the previous environment to the current one"""

        # Done this way since negative indexes are allowed
        if curr_env == 'dev':
            raise WrongEnvironmentError('There is no environment before '
                                        'the current environment (%s)'
                                        % curr_env)

        try:
            return self.env_order[self.env_order.index(curr_env) - 1]
        except ValueError:
            raise WrongEnvironmentError('Invalid environment: %s' % curr_env)


    def perform_deployments(self, args, pkg_id, app_host_map, app_dep_map):
        """ """

        # All is well, now do the deployment
        #   1. See if a deployment entry already exists in DB and use it,
        #      otherwise create a new one
        #   2. If deploying to tier, add an app deployment entry in DB
        #   3. Determine the appropriate hosts to deploy the application
        #   4. Do the deploy to the hosts
        dep_id = None
        pkg_deps = deploy.find_deployment_by_pkgid(pkg_id)

        if pkg_deps:
            last_pkg_dep = pkg_deps[0]

            if last_pkg_dep.dep_type == 'deploy':
                dep_id = last_pkg_dep.DeploymentID

        if dep_id is None:
            pkg_dep = deploy.add_deployment(pkg_id, args.user, 'deploy')
            dep_id = pkg_dep.DeploymentID

        self.deploy_to_hosts_or_tiers(args, dep_id, app_host_map, app_dep_map)


    def perform_invalidations(self, app_dep_map):
        """ """

        for app_id, dep_info in app_dep_map.iteritems():
            app_dep, app_type, dep_type, pkg = dep_info
            app_dep.status = 'invalidated'


    def perform_redeployments(self, args, dep_id, app_host_map, app_dep_map):
        """ """

        self.deploy_to_hosts_or_tiers(args, dep_id, app_host_map, app_dep_map,
                                      redeploy=True)


    def perform_restarts(self, args, dep_id, app_host_map, app_dep_map):
        """ """

        self.restart_hosts_or_tiers(args, dep_id, app_host_map, app_dep_map)


    def perform_rollbacks(self, args, app_pkg_map, app_dep_map):
        """ """

        # Since a roll back could end up at different versions for
        # each application tier, must do each tier on its own
        for app_id, pkg_id in app_pkg_map.iteritems():
            app_dep, app_type, dep_type, pkg = app_dep_map[app_id]
            app_id = app_dep.AppID

            pkg_dep = deploy.add_deployment(pkg_id, args.user, 'deploy')
            dep_id = pkg_dep.DeploymentID

            single_app_dep_map = { app_id : app_dep_map[app_id] }
            self.deploy_to_hosts_or_tiers(args, dep_id, None,
                                          single_app_dep_map)


    def perform_validations(self, args, app_dep_map):
        """ """

        for app_id, dep_info in app_dep_map.iteritems():
            app_dep, app_type, dep_type, pkg = dep_info

            # Commit to DB immediately
            Session.begin_nested()
            app_dep.status = 'validated'
            Session.commit()

            deploy.delete_host_deployments(args.project, app_dep.AppID,
                                           self.envs[args.environment])


    def process_mco_command(self, mco_cmd, retry):
        """Run a given MCollective 'mco' command"""

        print 'Running MCollective command:'
        print '    %s' % ' '.join(mco_cmd)

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

        print summary
        m = re.search(r'processing (\d+) / (\d+) ', summary)

        if m is None:
            return (False, 'Error parsing summary line.')

        # Virtual hosts in dev tend to time out unpredictably, probably
        # because vmware is slow to respond when the hosts are not
        # active. Subsequent retries after a timeout work better.
        if m.group(2) == '0' and retry > 0:
            print 'Discovery failure, trying again.'
            return self.process_mco_command(mco_cmd, retry-1)

        for host, hostinfo in mc_output.iteritems():
            if hostinfo['exitcode'] != 0:
                return (False, hostinfo['stderr'].strip())
            else:
                return (True, 'Deploy successful')

        return (False, 'Unknown/unparseable mcollective output: %s' %
                stdout)


    def restart_host(self, dep_host, app, retry=4):
        """Restart application on a given host"""

        mco_cmd = [ '/usr/bin/mco', 'tds', '--discovery-timeout', '4',
                    '--timeout', '60', '-W', 'hostname=%s' % dep_host,
                    app, 'restart' ]

        return self.process_mco_command(mco_cmd, retry)


    def restart_hosts(self, args, dep_hosts, dep_id):
        """Restart application on a given set of hosts"""

        failed_hosts = []

        for dep_host in dep_hosts:
            pkg = deploy.find_app_by_depid(dep_id)
            app = pkg.pkg_name

            success, info = self.restart_host(dep_host.hostname, app)

            if not success:
                failed_hosts.append((dep_host.hostname, info))

        # If any hosts failed, show failure information for each
        if failed_hosts:
            print 'Some hosts had failures:\n'

            for failed_host, reason in failed_hosts:
                print '-----'
                print 'Hostname: %s' % failed_host
                print 'Reason: %s' % reason


    def restart_hosts_or_tiers(self, args, dep_id, app_host_map, app_dep_map):
        """Restart the application on the requested hosts or application
           tiers
        """

        if getattr(args, 'hosts', None):
            hostnames = []

            for hosts in app_host_map.itervalues():
                hostnames.extend(hosts)

            dep_hosts = [ deploy.find_host_by_hostname(x) for x in hostnames ]
            self.restart_hosts(args, dep_hosts, dep_id)
        else:
            for app_id, dep_info in app_dep_map.iteritems():
                dep_hosts = deploy.find_hosts_for_app(app_id,
                                              self.envs[args.environment])
                self.restart_hosts(args, dep_hosts, dep_id)


    def send_notifications(self, args):
        """Send notifications for a given deployment"""

        msg_subject, msg_text = self.create_notifications(args)
        notification = tds.notifications.Notifications(args.user)
        notification.send_notifications(msg_subject, msg_text)


    def show_app_deployments(self, project, app_versions, env):
        """ """

        if not app_versions:
            print 'No deployments to tiers for this application ' \
                  '(for possible given version) yet'
            print 'in %s environment\n' % env
            return

        for app_type, version, revision in app_versions:
            print 'Deployment of %s to %s tier in %s environment:' \
                  % (project, app_type, env)
            print '==========\n'

            app_dep = deploy.list_app_deployment_info(project, env, app_type,
                                                      version, revision)

            dep, app_dep, pkg = app_dep

            print 'Version: %s-%s' % (pkg.version, pkg.revision)
            print 'Declared: %s' % dep.declared
            print 'Declaring user: %s' % dep.user
            print 'Realized: %s' % app_dep.realized
            print 'Realizing user: %s' % app_dep.user
            print 'App type: %s' % app_type
            print 'Environment: %s' % app_dep.environment
            print 'Deploy state: %s' % dep.dep_type
            print 'Install state: %s' % app_dep.status
            print ''


    def show_host_deployments(self, project, version, revision, env):
        """ """

        host_deps = deploy.list_host_deployment_info(project, env,
                                                     version=version,
                                                     revision=revision)

        if not host_deps:
            print 'No deployments to hosts for this application ' \
                  '(for possible given version)'
            print 'in %s environment\n' % env
        else:
            print 'Deployments of %s to hosts in %s environment:' \
                  % (project, env)
            print '==========\n'

            for dep, host_dep, hostname, pkg in host_deps:
                print 'Version: %s-%s' % (pkg.version, pkg.revision)
                print 'Declared: %s' % dep.declared
                print 'Declaring user: %s' % dep.user
                print 'Realized: %s' % host_dep.realized
                print 'Realizing user: %s' % host_dep.user
                print 'Hostname: %s' % hostname
                print 'Deploy state: %s' % dep.dep_type
                print 'Install state: %s' % host_dep.status
                print ''


    def verify_hosts(self, hosts, app_ids, environment):
        """Verify given hosts are in the correct environment and of the
           correct app IDs
        """

        valid_hostnames = {}
        app_id_hosts_mapping = {}

        for app_id in app_ids:
            app_id_hosts_mapping[app_id] = []

            try:
                hostnames = [ x.hostname for x in 
                              deploy.find_hosts_for_app(app_id, environment) ]
                valid_hostnames[app_id] = hostnames
            except DeployException:
                print e
                sys.exit(1)

        bad_hosts = []

        for hostname in hosts:
            for app_id in valid_hostnames.iterkeys():
                if hostname in valid_hostnames[app_id]:
                    app_id_hosts_mapping[app_id].append(hostname)
                    break
            else:
                bad_hosts.append(hostname)

        if bad_hosts:
            print 'The following hosts are in the wrong environment or ' \
                  'do not belong to a matching app type: %s' \
                  % ', '.join(bad_hosts)
            sys.exit(1)

        return app_id_hosts_mapping


    def verify_package(self, args, hostonly=False):
        """ """

        app_ids = self.get_app_types(args)
        pkg_id = self.get_package_id(args, app_ids, hostonly)

        if getattr(args, 'hosts', None):
            app_host_map = self.verify_hosts(args.hosts, app_ids,
                                             self.envs[args.environment])
            return (pkg_id, app_host_map)
        else:
            return (pkg_id, app_ids)


    def verify_project_type(self, project):
        """Ensure correct command is being used for given project"""

        try:
            # Tuple of one returned, just get the value
            project_type = repo.find_project_type(project)[0]
        except RepoException, e:
            print e
            sys.exit(1)

        if project_type not in self.valid_project_types:
            raise WrongProjectTypeError('Project "%s" is not valid for '
                                        'this command' % project)

        return project_type


    @catch_exceptions
    def invalidate(self, args):
        """ """

        tds.authorize.verify_access(args.user_level, args.environment)

        self.proj_type = self.verify_project_type(args.project)
        self.ensure_explicit_destinations(args)

        pkg_id, app_ids, app_host_map = self.get_app_info(args)
        app_dep_map = self.find_app_deployments(pkg_id, app_ids, args)

        if not len(filter(None, app_dep_map.itervalues())):
            print 'No deployments to invalidate for application "%s" ' \
                  'with version "%s" in %s environment' \
                  % (args.project, args.version, self.envs[args.environment])
            return

        app_dep_map = self.determine_invalidations(args, app_ids, app_dep_map)
        self.perform_invalidations(app_dep_map)

        Session.commit()


    @catch_exceptions
    def show(self, args):
        """ """

        tds.authorize.verify_access(args.user_level, 'dev')

        self.proj_type = self.verify_project_type(args.project)

        if args.version is None:
            app_versions = deploy.find_latest_deployed_version(args.project,
                                  self.envs[args.environment],
                                  apptypes=args.apptypes, apptier=True)
        else:
            app_versions = deploy.find_deployed_version(args.project,
                                                self.envs[args.environment],
                                                version=args.version,
                                                apptypes=args.apptypes,
                                                apptier=True)

        self.show_app_deployments(args.project, app_versions,
                                  self.envs[args.environment])
        # Revision is hardcoded to '1' for now
        self.show_host_deployments(args.project, args.version, '1',
                                   self.envs[args.environment])


    @catch_exceptions
    def validate(self, args):
        """ """

        tds.authorize.verify_access(args.user_level, args.environment)

        self.proj_type = self.verify_project_type(args.project)
        self.ensure_explicit_destinations(args)

        pkg_id, app_ids, app_host_map = self.get_app_info(args)
        app_dep_map = self.find_app_deployments(pkg_id, app_ids, args)

        if not len(filter(None, app_dep_map.itervalues())):
            print 'No deployments to validate for application "%s" ' \
                  'in %s environment' \
                  % (args.project, self.envs[args.environment])
            return

        app_dep_map = self.determine_validations(args, pkg_id, app_ids,
                                                 app_dep_map)
        self.perform_validations(args, app_dep_map)

        Session.commit()


class Config(BaseDeploy):
    """ """

    def __init__(self):
        """ """

        self.valid_project_types = [ 'tagconfig' ]


    def check_previous_environment(self, args, pkg_id, app_id):
        """Placeholder method as config projects don't check
           the previous environment for validation (due to
           differences in configuration information)
        """

        return True


    @catch_exceptions
    def add_apptype(self, args):
        """Add a specific app type to the given config project"""

        tds.authorize.verify_access(args.user_level, 'admin')

        self.proj_type = self.verify_project_type(args.project)

        try:
            app = repo.list_app_location(args.project)
            repo.add_app_packages_mapping(app.pkgLocationID, [args.apptype])
        except RepoException, e:
            print e
            return

        Session.commit()


    @catch_exceptions
    def create(self, args):
        """Add a new config project to the system"""

        tds.authorize.verify_access(args.user_level, 'admin')

        # Currently project type matches the project name
        if args.project not in self.valid_project_types:
            raise WrongProjectTypeError('Project "%s" is not valid for '
                                        'this command' % args.project)

        try:
            # Project type matches project name
            repo.add_app_location(args.project, args.buildtype,
                                  args.pkgname, args.project,
                                  args.pkgpath, args.buildhost,
                                  args.env_specific)
        except RepoException, e:
            print e
            return

        Session.commit()


    @catch_exceptions
    def delete(self, args):
        """Remove a config project from the system"""

        tds.authorize.verify_access(args.user_level, 'admin')

        self.proj_type = self.verify_project_type(args.project)

        try:
            repo.delete_app_location(args.project)
        except RepoException, e:
            print e
            return

        Session.commit()


    @catch_exceptions
    def delete_apptype(self, args):
        """Delete a specific app type from the given config project"""

        tds.authorize.verify_access(args.user_level, 'admin')

        self.proj_type = self.verify_project_type(args.project)

        try:
            app = repo.list_app_location(args.project)
            repo.delete_app_packages_mapping(app.pkgLocationID,
                                             [args.apptype])
        except RepoException, e:
            print e
            return

        Session.commit()


    @catch_exceptions
    def push(self, args):
        """ """

        tds.authorize.verify_access(args.user_level, args.environment)

        self.proj_type = self.verify_project_type(args.project)
        self.ensure_explicit_destinations(args)

        if not self.ensure_newer_versions(args):
            return

        pkg_id, app_ids, app_host_map = self.get_app_info(args)

        try:
            app_dep_map = self.find_app_deployments(pkg_id, app_ids, args)
        except NoCurrentDeploymentError, e:
            pass

        app_host_map, app_dep_map = \
            self.determine_new_deployments(args, pkg_id, app_ids,
                                           app_host_map, app_dep_map)
        self.send_notifications(args)
        self.perform_deployments(args, pkg_id, app_host_map, app_dep_map)

        Session.commit()


    @catch_exceptions
    def repush(self, args):
        """ """

        tds.authorize.verify_access(args.user_level, args.environment)

        self.proj_type = self.verify_project_type(args.project)
        self.ensure_explicit_destinations(args)

        pkg_id, app_ids, app_host_map = self.get_app_info(args, hostonly=True)
        app_dep_map = self.find_app_deployments(pkg_id, app_ids, args)

        if not len(filter(None, app_dep_map.itervalues())):
            print '%s to repush for configuration "%s" in %s environment' \
                  % (args.project, self.envs[args.environment])
            return

        dep_id = self.determine_redeployments(pkg_id)
        self.send_notifications(args)
        self.perform_redeployments(args, dep_id, app_host_map, app_dep_map)

        Session.commit()


    @catch_exceptions
    def revert(self, args):
        """ """

        tds.authorize.verify_access(args.user_level, args.environment)

        self.proj_type = self.verify_project_type(args.project)
        self.ensure_explicit_destinations(args)

        pkg_id, app_ids, app_host_map = self.get_app_info(args)
        app_dep_map = self.find_app_deployments(pkg_id, app_ids, args)

        if not len(filter(None, app_dep_map.itervalues())):
            print '%s to revert for configuration "%s" in %s environment' \
                  % (args.project, self.envs[args.environment])
            return

        # Commit to DB immediately
        Session.begin_nested()
        self.perform_invalidations(app_dep_map)
        Session.commit()

        app_pkg_map, app_dep_map = self.determine_rollbacks(args, app_ids,
                                                            app_dep_map)
        self.send_notifications(args)
        self.perform_rollbacks(self, args, app_pkg_map, app_dep_map)

        Session.commit()


class Deploy(BaseDeploy):
    """ """

    def __init__(self):
        """ """

        self.valid_project_types = [ 'application' ]


    def check_previous_environment(self, args, pkg_id, app_id):
        """Ensure deployment for previous environment for given package
           and apptier was validated; this is only relevant for staging
           and production environments
        """

        if args.environment != 'dev':
            prev_env = self.get_previous_environment(args.environment)
            prev_deps = deploy.find_app_deployment(pkg_id, [ app_id ],
                                                   self.envs[prev_env])
            # There should only be one deployment here
            prev_app_dep, prev_app_type, prev_dep_type, \
                prev_pkg = prev_deps[0]

            if (prev_dep_type != 'deploy' or
                prev_app_dep.status != 'validated'):
                print 'Application "%s" with version "%s" not fully ' \
                      'deployed or validated to previous environment ' \
                      '(%s) for apptype "%s"' \
                      % (args.project, args.version, prev_env, prev_app_type)
                return False

        return True


    @catch_exceptions
    def force_production(self, args):
        """ """

        tds.authorize.verify_access(args.user_level, 'admin')

        raise NotImplementedError('This subcommand is currently not '
                                  'implemented')


    @catch_exceptions
    def force_staging(self, args):
        """ """

        tds.authorize.verify_access(args.user_level, 'admin')

        raise NotImplementedError('This subcommand is currently not '
                                  'implemented')


    @catch_exceptions
    def promote(self, args):
        """ """

        tds.authorize.verify_access(args.user_level, args.environment)

        self.proj_type = self.verify_project_type(args.project)
        self.ensure_explicit_destinations(args)

        if not self.ensure_newer_versions(args):
            return

        pkg_id, app_ids, app_host_map = self.get_app_info(args)
        app_dep_map = self.find_app_deployments(pkg_id, app_ids, args)
        app_host_map, app_dep_map = \
            self.determine_new_deployments(args, pkg_id, app_ids,
                                           app_host_map, app_dep_map)
        self.send_notifications(args)
        self.perform_deployments(args, pkg_id, app_host_map, app_dep_map)

        Session.commit()


    @catch_exceptions
    def redeploy(self, args):
        """ """

        tds.authorize.verify_access(args.user_level, args.environment)

        self.proj_type = self.verify_project_type(args.project)
        self.ensure_explicit_destinations(args)

        pkg_id, app_ids, app_host_map = self.get_app_info(args, hostonly=True)
        app_dep_map = self.find_app_deployments(pkg_id, app_ids, args)

        if not len(filter(None, app_dep_map.itervalues())):
            print '%s to redeploy for application "%s" in %s environment' \
                  % (args.project, self.envs[args.environment])
            return

        dep_id = self.determine_redeployments(pkg_id)
        self.send_notifications(args)
        self.perform_redeployments(args, dep_id, app_host_map, app_dep_map)

        Session.commit()


    @catch_exceptions
    def restart(self, args):
        """ """

        tds.authorize.verify_access(args.user_level, args.environment)

        self.proj_type = self.verify_project_type(args.project)
        self.ensure_explicit_destinations(args)

        pkg_id, app_ids, app_host_map = self.get_app_info(args)
        app_dep_map = self.find_app_deployments(pkg_id, app_ids, args)

        if not len(filter(None, app_dep_map.itervalues())):
            print '%s to restart for application "%s" in %s environment' \
                  % (args.project, self.envs[args.environment])
            return

        dep_id = self.determine_restarts(pkg_id)
        self.perform_restarts(args, dep_id, app_host_map, app_dep_map)


    @catch_exceptions
    def rollback(self, args):
        """ """

        tds.authorize.verify_access(args.user_level, args.environment)

        self.proj_type = self.verify_project_type(args.project)
        self.ensure_explicit_destinations(args)

        pkg_id, app_ids, app_host_map = self.get_app_info(args)
        app_dep_map = self.find_app_deployments(pkg_id, app_ids, args)

        if not len(filter(None, app_dep_map.itervalues())):
            print '%s to roll back for application "%s" in %s environment' \
                  % (args.project, self.envs[args.environment])
            return

        # Commit to DB immediately
        Session.begin_nested()
        self.perform_invalidations(app_dep_map)
        Session.commit()

        app_pkg_map, app_dep_map = self.determine_rollbacks(args, app_ids,
                                                            app_dep_map)
        self.send_notifications(args)
        self.perform_rollbacks(args, app_pkg_map, app_dep_map)

        Session.commit()
