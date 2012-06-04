from tagopsdb.database import init_session
from tagopsdb.database.meta import Session
from tagopsdb.exceptions import RepoException

import tagopsdb.deploy.repo as repo
#import tagopsdb.deploy.package as package
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
            print "Project: %s" % app.app_name
            print "Project type: %s" % app.pkg_type
            print "Package name: %s" % app.pkg_name
            print "Path: %s" % app.path

            if app.environment:
                is_env = 'Yes'
            else:
                is_env = 'No'

            print "Environment specific: %s" % is_env
            print ""


class Package(object):
    """ """

    def __init__(self):
        """ """

        init_session()


    def add(self, args):
        """ """

        verify_access('dev')


    def delete(self,args):
        """ """

        verify_access('dev')


    def list(self, args):
        """ """

        verify_access('dev')


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
