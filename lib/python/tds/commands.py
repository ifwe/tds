import os
import signal
import socket

import beanstalkc

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
                                           args.buildhost, args.environment)
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

            app_defs = repo.find_app_packages_mapping(app.pkgLocationID)
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


    @catch_exceptions
    def force_production(self, args):
        """ """

        verify_access(args.user_level, 'admin')


    @catch_exceptions
    def force_staging(self, args):
        """ """

        verify_access(args.user_level, 'admin')


    @catch_exceptions
    def invalidate(self, args):
        """ """

        verify_access(args.user_level, args.environment)

        #try:
        #    dep = deploy.get_deployment_by_id(args.deployid)
        #    self.check_environment(self.envs[args.environment],
        #                           dep.environment)
        #    deploy.invalidate_deployment(dep, args.user)
        #except DeployException, e:
        #    print e
        #    return

        #Session.commit()


    @catch_exceptions
    def promote(self, args):
        """ """

        verify_access(args.user_level, args.environment)

        # Get package ID
        try:
            # Revision hardcoded to '1' for now
            pkg = package.find_package(args.project, args.version, '1')
            if not pkg:
                print 'Application "%s" with version "%s" not available ' \
                      'in the repository.' % (args.project, args.version)
                return
        except PackageException, e:
            print e
            return

        pkg_id = pkg.PackageID

        # Determine relevant application IDs
        app_ids = [ x.AppID for x
                    in repo.find_app_packages_mapping(args.project) ]

        if args.apptypes:
            app_defs = [ repo.find_app_by_apptype(x) for x in args.apptypes ]
            new_app_ids = [ x.AppID for x in app_defs ]

            if set(new_app_ids).issubset(set(app_ids)):
                app_ids = new_app_ids
            else:
                print 'One of the app types given is not a valid app type ' \
                      'for the current deployment'
                return

        # Determine environment for deployment, ensure
        # the correct deploy server is in use
        deps = deploy.find_app_deployment(pkg_id, app_ids,
                                          self.envs[args.environment])

        if deps:
            last_dep, last_dep_type = deps[0]

            if last_dep_type == 'deploy':
                raise WrongEnvironmentError(
                      'Application "%s" with version "%s" already deployed '
                      'to this environment (%s)' % (args.project,
                      args.version, self.envs[args.environment]))

        if args.environment != 'dev':
            prev_environment = self.get_previous_environment(args.environment)
            deps = deploy.find_app_deployment(pkg_id, app_ids,
                                              self.envs[prev_environment])
            last_dep, last_dep_type = deps[0]

            if last_dep_type != 'deploy' or last_dep.status != 'validated':
                print 'Application "%s" with version "%s" not properly ' \
                      'or fully deployed to previous environment (%s)' \
                      % (args.project, args.version, prev_environment)
                return

        # All is well, start deployment
        dep_id = None
        deps = deploy.find_deployment_by_pkgid(pkg_id)

        if deps:
            last_dep = deps[0]

            if last_dep.dep_type == 'deploy':
                dep_id = last_dep.DeploymentID

        if dep_id is None:
            dep = deploy.add_deployment(pkg_id, args.user, 'deploy')
            dep_id = dep.DeploymentID

        if args.apptypes:
            for app_id in app_ids:
                deploy.add_app_deployment(dep_id, app_id, args.user,
                                          'incomplete',
                                          self.envs[args.environment])
                dep_hosts = deploy.find_hosts_for_app(app_id)

                for dep_host in dep_hosts:
                    if deploy.find_host_deployment_by_depid(dep_id,
                                                        dep_host.hostname):
                        continue

                    # For now, just set entry in host_deployments to 'ok'
                    deploy.add_host_deployment(dep_id, dep_host.HostID,
                                               args.user, 'ok')
        elif args.hosts:
            dep_hosts = [ deploy.find_host_by_hostname(x) for x
                          in args.hosts]

            for dep_host in dep_hosts:
                if deploy.find_host_deployment_by_depid(dep_id,
                                                        dep_host.hostname):
                    continue

                # For now, just set entry in host_deployments to 'ok'
                deploy.add_host_deployment(dep_id, dep_host.HostID,
                                           args.user, 'ok')
        else:
            for app_id in app_ids:
                deploy.add_app_deployment(dep_id, app_id, args.user,
                                          'incomplete',
                                          self.envs[args.environment])
                dep_hosts = deploy.find_hosts_for_app(app_id,
                                                  self.envs[args.environment])

                for dep_host in dep_hosts:
                    if deploy.find_host_deployment_by_depid(dep_id,
                                                        dep_host.hostname):
                        continue

                    # For now, just set entry in host_deployments to 'ok'
                    deploy.add_host_deployment(dep_id, dep_host.HostID,
                                               args.user, 'ok')

        Session.commit()


    @catch_exceptions
    def redeploy(self, args):
        """ """

        verify_access(args.user_level, args.environment)


    @catch_exceptions
    def rollback(self, args):
        """ """

        verify_access(args.user_level, args.environment)

        # Do rollback

        if not args.remain_valid:
            # Perform invalidation
            self.invalidate(args)


    @catch_exceptions
    def show(self, args):
        """ """

        verify_access(args.user_level, 'dev')

        # Revision hardcoded to '1' for now
        app_deps, host_deps = deploy.list_deployment_info(args.project,
                                                          args.version,
                                                          '1')

        print 'Deployments of %s to tiers:' % args.project
        print '==========\n'

        if not app_deps:
            print 'No deployments to tiers for this version and revision\n'
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

        if not host_deps:
            print 'No deployments to hosts for this version and revision\n'
        else:
            for dep, host_dep, hostname in host_deps:
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

        # Get package ID
        try:
            # Revision hardcoded to '1' for now
            pkg = package.find_package(args.project, args.version, '1')
            if not pkg:
                print 'Application "%s" with version "%s" not available ' \
                      'in the repository.' % (args.project, args.version)
                return
        except PackageException, e:
            print e
            return

        pkg_id = pkg.PackageID

        # Determine relevant application IDs
        app_ids = [ x.AppID for x
                    in repo.find_app_packages_mapping(args.project) ]

        if args.apptypes:
            app_defs = [ repo.find_app_by_apptype(x) for x in args.apptypes ]
            new_app_ids = [ x.AppID for x in app_defs ]

            if set(new_app_ids).issubset(set(app_ids)):
                app_ids = new_app_ids
            else:
                print 'One of the app types given is not a valid app type ' \
                      'for the current deployment'
                return

        # Get relevant deployments, validate and clean host deployments
        deps = deploy.find_app_deployment(pkg_id, app_ids,
                                          self.envs[args.environment])

        if not deps:
            print 'No deployments to validate for application "%s" ' \
                  'with version "%s" in %s environment' \
                  % (args.project, args.version, self.envs[args.environment])
            return

        for dep in deps:
            app_dep, app_type, dep_type = dep

            if app_dep.status == 'validated':
                print 'Deployment for application "%s" with version "%s" ' \
                      'for apptype "%s" already validated in %s environment' \
                      % (args.project, args.version, app_type,
                         self.envs[args.environment])
                continue

            not_ok_hosts = deploy.find_host_deployments_not_ok(pkg_id,
                                  app_dep.AppID, self.envs[args.environment])
            hostnames = [ x[1] for x in not_ok_hosts ]

            if not_ok_hosts:
                print 'Some hosts for deployment for application "%s" ' \
                      'with version "%s" for apptype "%s" are not in ' \
                      'an "ok" state:' \
                      % (args.project, args.version, app_type)
                print '    %s' % ', '.join(hostnames)
                continue

            app_dep.status = 'validated'
            deploy.delete_host_deployments(app_dep.AppID,
                                           self.envs[args.environment])

        Session.commit()
