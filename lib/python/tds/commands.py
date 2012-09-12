import os
import re
import signal
import socket
import subprocess

import beanstalkc
import json

from tagopsdb.database.meta import Session
from tagopsdb.exceptions import RepoException, PackageException, \
                                DeployException, NotImplementedException

import tagopsdb.deploy.repo as repo
import tagopsdb.deploy.package as package
import tagopsdb.deploy.deploy as deploy

from tds.authorize import verify_access
from tds.exceptions import NotImplementedError, WrongEnvironmentError


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

        verify_access(args.user_level, 'admin')

        try:
            loc_id = repo.add_app_location(args.buildtype, args.pkgname,
                                           args.project, args.pkgpath,
                                           args.buildhost, args.env_specific)
            repo.add_app_packages_mapping(loc_id, args.apptypes)
        except RepoException, e:
            print e
            return

        Session.commit()


    @catch_exceptions
    def delete(self, args):
        """ """

        verify_access(args.user_level, 'admin')

        try:
            repo.delete_app_location(args.project)
        except RepoException, e:
            print e
            return

        Session.commit()


    @catch_exceptions
    def list(self, args):
        """ """

        verify_access(args.user_level, 'dev')

        for app in repo.list_all_app_locations():
            print 'Project: %s' % app.app_name
            print 'Project type: %s' % app.pkg_type
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
        self.bean_id = "%s-%s" % (self.host, os.getpid())
        self.job = None


    def beanstalk_handler(self, signum, frame):
        """ """

        # Release any currently held job
        if self.job:
            self.job.release()

        raise PackageException('The requested job response from the '
                               'beanstalk server was never received.\n'
                               'Please contact SiteOps for assistance.')


    @catch_exceptions
    def add(self, args):
        """ """

        verify_access(args.user_level, 'dev')

        try:
            # The real 'revision' is hardcoded to 1 for now
            # This needs to be changed at some point
            package.add_package(args.project, args.version, '1', args.user)
        except PackageException, e:
            print e
            return

        # Get build server for package
        build_host = repo.list_app_location(args.project).build_host

        beanstalk = beanstalkc.Connection(host='tong01.tagged.com',
                                          port=11300)
        beanstalk.use('tds.package.copy.%s' % build_host)
        beanstalk.watch('tds.package.error')
        beanstalk.ignore('default')

        beanstalk.put('%s %s %s' % (self.bean_id, args.project,
                                    args.version))

        print "Sent job to %s, waiting for response..." % build_host
        # Watch error tube for responses, react accordingly
        # A timeout will occur if no valid messages are received
        # within specified amount of time

        signal.signal(signal.SIGALRM, self.beanstalk_handler)
        signal.alarm(20)

        while True:
            self.job = beanstalk.reserve()
            id, result, msg = self.job.body.split(' ', 2)

            # Make sure this is for our client
            # print "ID: %s, Bean ID: %s" % (id, self.bean_id)
            if id == self.bean_id:
                break

            self.job.release()

        signal.alarm(0)

        # Safe to remove job now
        self.job.delete()

        if result == 'OK':
            Session.commit()
            print 'Added package for project "%s", version %s' \
                  % (args.project, args.version)
        elif result == 'ERROR':
            Session.rollback()
            print 'Unable to add package for project "%s", version %s' \
                  % (args.project, args.version)
            print 'Error: %s' % msg
        else:
            # Unexpected result
            Session.rollback()
            print 'Unable to add package for project "%s", version %s' \
                  % (args.project, args.version)
            print 'Unexpected result: %s, %s' % (result, msg)


    @catch_exceptions
    def delete(self,args):
        """ """

        verify_access(args.user_level, 'dev')

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

        verify_access(args.user_level, 'dev')

        for pkg in package.list_packages():
            print 'Project: %s' % pkg.pkg_name
            print 'Version: %s' % pkg.version
            print 'Revision: %s' % pkg.revision
            print ''


class Deploy(object):
    """ """

    envs = { 'dev' : 'development',
             'stage' : 'staging',
             'prod' : 'production', }
    env_order = [ 'dev', 'stage', 'prod' ]


    def __init__(self):
        """ """

        pass


    def check_environment(self, curr_env, req_env):
        """Verify command is being run from correct environment"""

        if req_env != curr_env:
            raise WrongEnvironmentError('This command must be run from '
                                        'the %s deploy server.' % req_env)

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


    def deploy_to_host(self, dep_host, app, version):
        """Deploy specified package to a given host"""

        mco_cmd = [ '/usr/bin/mco', 'tds', '--discovery-timeout', '2',
                    '--timeout', '60', '-W', 'hostname=%s' % dep_host,
                    app, version ]
        print "running mcollective command:"
        print " ".join(mco_cmd)

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

        for host, hostinfo in mc_output.iteritems():
            if hostinfo['exitcode'] != 0:
                return (False, hostinfo['stderr'].strip())
            else:
                return (True, 'Deploy successful')


    def deploy_to_hosts(self, dep_hosts, dep_id, user, redeploy=False):
        """Perform deployment on given set of hosts (only doing those
           that previously failed with a redeploy)
        """

        failed_hosts = []

        for dep_host in dep_hosts:
            pkg = deploy.find_app_by_depid(dep_id)
            app, version = pkg.pkg_name, pkg.version

            host_dep = deploy.find_host_deployment_by_depid(dep_id, dep_host.hostname)

            if redeploy and host_dep and host_dep.status != 'ok':
                success, info = self.deploy_to_host(dep_host, app, version)

                if success:
                    host_dep.status = 'ok'
                else:
                    failed_hosts.append((dep_host, info))
            else:
                host_dep = deploy.add_host_deployment(dep_id, dep_host.HostID,
                                                      user, 'incomplete')
                success, info = self.deploy_to_host(dep_host.hostname, app, version)

                if success:
                    host_dep.status = 'ok'
                else:
                    host_dep.status = 'failed'
                    failed_hosts.append((dep_host.hostname, info))

        # If any hosts failed, show failure information for each
        if failed_hosts:
            print 'Some hosts had failures:\n'

            for failed_host, reason in failed_hosts:
                print '-----'
                print 'Hostname: %s' % failed_host
                print 'Reason: %s' % reason


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


    def get_package_id(self, args):
        """Get the package ID for the current project and version
           (or most recent deployed version if none is given)
        """

        if hasattr(args, 'version'):
            version = args.version
        else:
            # Must determine latest deployed version
            # (Note: this currently only works for projects
            #  with a single app type)
            version = deploy.find_latest_deployed_version(args.project,
                                                          apptier=True)

        try:
            # Revision hardcoded to '1' for now
            pkg = package.find_package(args.project, version, '1')
            if not pkg:
                print 'Application "%s" with version "%s" not ' \
                      'available in the repository.' % (args.project, version)
                return
        except PackageException, e:
            print e
            sys.exit(1)

        return pkg.PackageID


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


    def verify_package(self, args):
        """ """

        pkg_id = self.get_package_id(args)

        app_ids = self.get_app_types(args)

        if getattr(args, 'hosts', None):
            app_host_map = self.verify_hosts(args.hosts, app_ids,
                                             self.envs[args.environment])
            return (pkg_id, app_host_map)
        else:
            return (pkg_id, app_ids)


    @catch_exceptions
    def force_production(self, args):
        """ """

        verify_access(args.user_level, 'admin')

        raise NotImplementedError('This subcommand is currently not '
                                  'implemented')


    @catch_exceptions
    def force_staging(self, args):
        """ """

        verify_access(args.user_level, 'admin')

        raise NotImplementedError('This subcommand is currently not '
                                  'implemented')


    @catch_exceptions
    def invalidate(self, args):
        """ """

        verify_access(args.user_level, args.environment)

        pkg_id, app_ids = self.verify_package(args)

        # Get relevant deployments, ensure each was validated
        # then invalidate
        deps = deploy.find_app_deployment(pkg_id, app_ids,
                                          self.envs[args.environment])

        if not deps:
            print 'No deployments to invalidate for application "%s" ' \
                  'with version "%s" in %s environment' \
                  % (args.project, args.version, self.envs[args.environment])
            return

        for dep in deps:
            app_dep, app_type, dep_type = dep

            if app_dep.status != 'validated':
                print 'Deployment for application "%s" with version "%s" ' \
                      'for apptype "%s" has not been validated in %s ' \
                      'environment' % (args.project, args.version,
                                       app_type, self.envs[args.environment])
                continue

            app_dep.status = 'invalidated'

        Session.commit()


    @catch_exceptions
    def promote(self, args):
        """ """

        verify_access(args.user_level, args.environment)

        if args.hosts:
            pkg_id, app_host_map = self.verify_package(args)
            host_deps = find_host_deployment_by_project(args.project,
                                                        args.hosts)

            for host_dep, hostname, app_id, dep_version in host_deps:
                if dep_version == args.version and host_dep.status == 'ok':
                    print 'Application "%s" with version "%s" already ' \
                          'deployed to host "%s"' \
                          % (args.project, args.version, hostname)
                    app_host_map[app_id].remove(hostname)

                    if not app_host_map[app_id]:
                        del app_host_map[app_id]

                app_ids = app_host_map.keys()
        else:
            pkg_id, app_ids = self.verify_package(args)

        deps = deploy.find_app_deployment(pkg_id, app_ids,
                                          self.envs[args.environment])
        app_dep_map = {}

        for app_id in app_ids:
            app_dep_map[app_id] = None

        for app_dep, app_type, dep_type in deps:
            app_dep_map[app_dep.AppID] = (app_dep, app_type, dep_type)

        for app_id in app_ids:
            ok = True

            if args.environment != 'dev':
                prev_env = self.get_previous_environment(args.environment)
                prev_deps = deploy.find_app_deployment(pkg_id,
                                                  [ app_dep.AppID ],
                                                  self.envs[prev_environment])
                # There should only be one deployment here
                prev_app_dep, prev_app_type, prev_dep_type = prev_deps[0]

                if (prev_dep_type != 'deploy' or
                    prev_app_dep.status != 'validated'):
                    print 'Application "%s" with version "%s" not properly ' \
                        'or fully deployed to previous environment (%s) ' \
                        'for apptype "%s"' \
                        % (args.project, args.version, prev_environment,
                           prev_app_type)
                    ok = False

            if ok:
                if not app_dep_map[app_id]:
                    continue

                dep = app_dep_map[app_id]
                app_dep, app_type, dep_type = dep

                if dep_type == 'deploy':
                    print 'Application "%s" with version "%s" already ' \
                          'deployed to this environment (%s) for ' \
                          'apptype "%s"' \
                          % (args.project, args.version,
                             self.envs[args.environment], app_type)
                    ok = False

            if not ok:
                if args.hosts:
                    del app_host_map[app_id]
                else:
                    del app_dep_map[app_id]

        # All is well, start deployment
        dep_id = None
        pkg_deps = deploy.find_deployment_by_pkgid(pkg_id)

        if pkg_deps:
            last_pkg_dep = pkg_deps[0]

            if last_pkg_dep.dep_type == 'deploy':
                dep_id = last_pkg_dep.DeploymentID

        if dep_id is None:
            pkg_dep = deploy.add_deployment(pkg_id, args.user, 'deploy')
            dep_id = pkg_dep.DeploymentID

        if args.hosts:
            hostnames = []

            for hosts in app_host_map.itervalues():
                hostnames.extend(hosts)

            dep_hosts = [ deploy.find_host_by_hostname(x) for x in hostnames ]
            self.deploy_to_hosts(dep_hosts, dep_id, args.user)
        else:
            for app_id in app_dep_map.iterkeys():
                deploy.add_app_deployment(dep_id, app_id, args.user,
                                          'incomplete',
                                          self.envs[args.environment])
                dep_hosts = deploy.find_hosts_for_app(app_id,
                                          self.envs[args.environment])
                self.deploy_to_hosts(dep_hosts, dep_id, args.user)

        Session.commit()


    @catch_exceptions
    def redeploy(self, args):
        """ """

        verify_access(args.user_level, args.environment)

        raise NotImplementedError('This subcommand is currently not '
                                  'implemented')

        pkg_id = self.get_package_id(args)
        app_ids = self.get_app_types(args)

        # If hosts have been defined, verify they're in the correct
        # environment and have a matching deploy to do the redeploy
        # for, otherwise check each app type for a matching deploy
        if args.hosts:
            valid_hosts, app_host_map = self.verify_hosts(args.hosts,
                                             app_ids,
                                             self.envs[args.environment])

            host_deps = find_host_deployment_by_pkgid(pkg_id, valid_hosts)
            # Second element is hostname
            host_match = [ x[1] for x in host_deps ]

            app_ids = app_host_map.keys()
            app_deps = deploy.find_app_deployment(pkg_id, app_ids,
                                                  self.envs[args.environment])
            # First element is app ID
            host_match.extend([ app_host_map[x[0]] for x in app_deps ])

            bad_hosts = []

            for valid_host in valid_hosts:
                if valid_host not in host_match:
                    bad_hosts.append(valid_host)

            if bad_hosts:
                print 'Application "%s" with version "%s" has not been ' \
                      'deployed to the following hosts yet: %s' \
                      % ', '.join(bad_hosts)
                return
        else:
            app_deps = deploy.find_app_deployment(pkg_id, app_ids,
                                                  self.envs[args.environment])
            # Second element is app type
            app_match = [ x[1] for x in app_deps ]

            bad_apps = []

            for app_type in args.apptypes:
                if app_type not in app_match:
                    bad_apps.append(app_type)

            if bad_apps:
                print 'Application "%s" with version "%s" has not been ' \
                      'deployed to the following app types yet: %s' \
                      % ', '.join(bad_apps)
                return

        # All is well, start redeployment
        pkg_deps = deploy.find_deployment_by_pkgid(pkg_id)
        last_pkg_dep = pkg_deps[0]  # Guaranteed to have at least one

        if last_pkg_dep.dep_type == 'deploy':
            dep_id = last_pkg_dep.DeploymentID
        else:
            # Deploy type is 'rollback', create new deployment table entry
            pkg_dep = deploy.add_deployment(pkg_id, args.user, 'deploy')
            dep_id = pkg_dep.DeploymentID

        if args.hosts:
            dep_hosts = [ deploy.find_host_by_hostname(x)
                          for x in valid_hosts ]
            self.deploy_to_hosts(dep_hosts, dep_id, args.user)
        else:
            for app_id in app_ids:
                dep_hosts = deploy.find_hosts_for_app(app_id,
                                          self.envs[args.environment])
                self.deploy_to_hosts(dep_hosts, dep_id, args.user,
                                     redeploy=True)

        Session.commit()


    @catch_exceptions
    def rollback(self, args):
        """ """

        verify_access(args.user_level, args.environment)

        pkg_id, app_ids = self.verify_package(args)

        # Get relevant deployment, invalidate, and deploy previous
        # validated version
        deps = deploy.find_app_deployment(pkg_id, app_ids,
                                          self.envs[args.environment])

        if not deps:
            print 'No deployments to roll back for application "%s" ' \
                  'in %s environment' \
                  % (args.project, self.envs[args.environment])
            return

        for dep in deps:
            app_dep, app_type, dep_type = dep
            app_id = app_dep.AppID

            app_dep.status = 'invalidated'
            Session.flush()   # Needed to push change for status (yes, hack)

            last_app_dep, pkg_id = \
                deploy.find_latest_validated_deployment(args.project, app_id)

            if pkg_id is None:
                print 'No previous deployment to roll back to for ' \
                      'application "%s" for app type "%s" in %s ' \
                      'environment' % (args.project, app_id,
                                       self.envs[args.environment])
                continue

            pkg_dep = deploy.add_deployment(pkg_id, args.user, 'deploy')
            dep_id = pkg_dep.DeploymentID

            deploy.add_app_deployment(dep_id, app_id, args.user,
                                      'incomplete',
                                      self.envs[args.environment])
            dep_hosts = deploy.find_hosts_for_app(app_id,
                                      self.envs[args.environment])
            self.deploy_to_hosts(dep_hosts, dep_id, args.user)

        Session.commit()


    @catch_exceptions
    def show(self, args):
        """ """

        verify_access(args.user_level, 'dev')

        if args.version is None:
            app_version = deploy.find_latest_deployed_version(args.project,
                                                              apptier=True)
        else:
            app_version = args.version

        print 'App version is "%s"' % app_version
        print 'Deployments of %s to tiers:' % args.project
        print '==========\n'

        if app_version is None:
            print 'No deployments to tiers for this application yet\n'
        else:
            # Revision hardcoded to '1' for now
            app_deps = deploy.list_app_deployment_info(args.project,
                                                       app_version,
                                                       '1')

            if not app_deps:
                print 'No deployments to tiers for this application with ' \
                      'given version and revision\n'
            else:
                for dep, app_dep, app_type in app_deps:
                    print 'Declared: %s' % dep.declared
                    print 'Declaring user: %s' % dep.user
                    print 'Realized: %s' % app_dep.realized
                    print 'Realizing user: %s' % app_dep.user
                    print 'App type: %s' % app_type
                    print 'Environment: %s' % app_dep.environment
                    print 'Deploy state: %s' % dep.dep_type
                    print 'Install state: %s' % app_dep.status
                    print ''

        print 'Deployments of %s to hosts:' % args.project
        print '==========\n'

        host_deps = deploy.list_host_deployment_info(args.project,
                version = args.version)

        if not host_deps:
            print 'No deployments to hosts for this application with ' \
                  'given version and revision\n'
        else:
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


    @catch_exceptions
    def validate(self, args):
        """ """

        verify_access(args.user_level, args.environment)

        pkg_info = self.verify_package(args)
        if pkg_info is None:
            return # already printed error in verify_package()

        pkg_id, app_ids = pkg_info

        # Get relevant deployments, validate and clean host deployments
        deps = deploy.find_app_deployment(pkg_id, app_ids,
                                          self.envs[args.environment])

        if not deps:
            print 'No deployments to validate for application "%s" ' \
                  'in %s environment' \
                  % (args.project, self.envs[args.environment])
            return

        for dep in deps:
            app_dep, app_type, dep_type = dep

            if app_dep.status == 'validated':
                print 'Deployment for application "%s" for apptype "%s" ' \
                      'already validated in %s environment' \
                      % (args.project, app_type, self.envs[args.environment])
                continue

            not_ok_hosts = deploy.find_host_deployments_not_ok(pkg_id,
                                  app_dep.AppID, self.envs[args.environment])
            hostnames = [ x[1] for x in not_ok_hosts ]

            if not_ok_hosts and not args.force:
                print 'Some hosts for deployment for application "%s" ' \
                      'for apptype "%s" are not in an "ok" state:' \
                      % (args.project, app_type)
                print '    %s' % ', '.join(hostnames)
                continue

            app_dep.status = 'validated'
            deploy.delete_host_deployments(app_dep.AppID,
                                           self.envs[args.environment])

        Session.commit()
