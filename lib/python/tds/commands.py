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

        self.bean_id = "%s-%s" % (socket.gethostname(), os.getpid())


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

        beanstalk = beanstalkc.Connection(host='tong01.tagged.com',
                                          port=11300)
        beanstalk.use('tds.package.copy')
        beanstalk.watch('tds.package.error')
        beanstalk.ignore('default')

        beanstalk.put('%s %s %s' % (self.bean_id, args.project,
                                    args.revision))

        # Watch error tube for responses, react accordingly
        while True:
            job = beanstalk.reserve()
            id, result, msg = job.body.split(' ', 3)

            # Make sure this is for our client
            if id == self.bean_id:
                break

            job.release()

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

        for dep_info, pkg_info, app_type in deploy.list_deployment_info(
                                                   args.project,
                                                   args.revision):
            rpm_name = '%s-%s-%s.noarch.rpm' % (pkg_info.pkg_name,
                                                pkg_info.version,
                                                pkg_info.revision)
            dep_date = dep_info.declared.isoformat()

            print 'Deployment ID: %s' % dep_info.DeploymentID
            print 'Package name: %s' % rpm_name
            print 'Declaration: %s' % dep_info.declaration
            print 'Environment: %s' % dep_info.environment
            print 'Deploy date: %s' % dep_date
            print 'Declarer: %s' % dep_info.declarer
            print 'App type: %s' % app_type
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
