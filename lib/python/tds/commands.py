import os
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
        repo.add_app_location(args.buildtype, args.pkgname, args.project,
                              args.pkgpath, args.buildhost, args.environment)
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


    @catch_exceptions
    def add(self, args):
        """ """

        verify_access(args.user_level, 'dev')

        try:
            # The real 'revision' is hardcoded to 1 for now
            # This needs to be changed at some point
            package.add_package(args.project, args.revision, '1', args.user)
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
                                    args.revision))

        # Watch error tube for responses, react accordingly
        while True:
            job = beanstalk.reserve()
            id, result, msg = job.body.split(' ', 2)

            # Make sure this is for our client
            # print "ID: %s, Bean ID: %s" % (id, self.bean_id)
            if id == self.bean_id:
                break

            job.release()

        # Safe to remove job now
        job.delete()

        if result == 'OK':
            Session.commit()
            print 'Added package for project "%s", version %s' \
                  % (args.project, args.revision)
        elif result == 'ERROR':
            Session.rollback()
            print 'Unable to add package for project "%s", version %s' \
                  % (args.project, args.revision)
            print 'Error: %s' % msg
        else:
            # Unexpected result
            Session.rollback()
            print 'Unable to add package for project "%s", version %s' \
                  % (args.project, args.revision)
            print 'Unexpected result: %s, %s' % (result, msg)


    @catch_exceptions
    def delete(self,args):
        """ """

        verify_access(args.user_level, 'dev')

        try:
            # The real 'revision' is hardcoded to 1 for now
            # This needs to be changed at some point
            package.delete_package(args.project, args.revision, '1')
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


    def __init__(self):
        """ """

        pass


    def check_environment(self, curr_env, req_env):
        """Verify command is being run from correct environment"""

        if req_env != curr_env:
            raise WrongEnvironmentError('This command must be run from '
                                        'the %s deploy server.' % req_env)


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

        try:
            dep = deploy.get_deployment_by_id(args.deployid)
            self.check_environment(self.envs[args.environment],
                                   dep.environment)
            deploy.invalidate_deployment(dep, args.user)
        except DeployException, e:
            print e
            return

        Session.commit()


    @catch_exceptions
    def promote(self, args):
        """ """

        verify_access(args.user_level, args.environment)


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

        try:
            dep = deploy.get_deployment_by_id(args.deployid)
            self.check_environment(self.envs[args.environment],
                                   dep.environment)
            deploy.validate_deployment(dep, args.user)
        except DeployException, e:
            print e
            return

        Session.commit()
