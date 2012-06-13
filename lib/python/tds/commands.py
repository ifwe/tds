import beanstalkc

from tagopsdb.database import init_session
from tagopsdb.database.meta import Session
from tagopsdb.exceptions import RepoException

import tagopsdb.deploy.repo as repo
import tagopsdb.deploy.package as package
#import tagopsdb.deploy.deploy as deploy

from tds.authorize import verify_access


class Repository(object):
    """ """

    def __init__(self):
        """ """

        init_session()


    def add(self, args):
        """ """

        verify_access('admin')
        repo.add_app_location(args.buildtype, args.pkgname, args.project,
                              args.pkgpath, args.environment)
        Session.commit()


    def delete(self, args):
        """ """

        verify_access('admin')

        try:
            repo.delete_app_location(args.project)
        except RepoException, e:
            print e
            return

        Session.commit()


    def list(self, args):
        """ """

        verify_access('dev')

        for app in repo.list_all_app_locations():
            print 'Project: %s' % app.app_name
            print 'Project type: %s' % app.pkg_type
            print 'Package name: %s' % app.pkg_name
            print 'Path: %s' % app.path

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

        init_session()


    def add(self, args):
        """ """

        verify_access('dev')

        try:
            # The real 'revision' is hardcoded to 1 for now
            # This needs to be changed at some point
            package.add_package(args.project, args.revision, '1', args.user)
        except PackageException, e:
            print e
            return

        beanstalk = beanstalkc.Connection(host='tong01.tagged.com',
                                          port=14711)
        beanstalk.use('tds.package.copy')
        beanstalk.watch('tds.package.error')
        beanstalk.ignore('default')

        beanstalk.put('%s %s %s' % (self.bean_id, args.project, args.revision)

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


    def delete(self,args):
        """ """

        verify_access('dev')

        try:
            # The real 'revision' is hardcoded to 1 for now
            # This needs to be changed at some point
            repo.delete_package(args.project, args.revision, '1')
        except PackageException, e:
            print e
            return

        Session.commit()


    def list(self, args):
        """ """

        verify_access('dev')

        for pkg in package.list_packages():
            print 'Project: %s' % pkg.pkg_name
            print 'Version: %s' % pkg.version
            print 'Revision: %s' % pkg.revision


class Deploy(object):
    """ """

    def __init__(self):
        """ """

        init_session()


    def force_production(self, args):
        """ """

        verify_access('admin')


    def force_staging(self, args):
        """ """

        verify_access('admin')


    def promote(self, args):
        """ """

        verify_access('dev')


    def redeploy(self, args):
        """ """

        verify_access('dev')


    def rollback(self, args):
        """ """

        verify_access('dev')


    def show(self, args):
        """ """

        verify_access('dev')


    def validate(self, args):
        """ """

        verify_access('dev')
