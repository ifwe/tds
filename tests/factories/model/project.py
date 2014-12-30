'''
Factories to create various tds.model.project.Project instances
'''
import factory
import tds.model.project as p
from .application import ApplicationFactory
# from .deploy_target import AppTargetFactory
#
# class _ProjectDelegate(object):
#     targets = [AppTargetFactory(name="targ1"),
#                AppTargetFactory(name="targ2")]


class ProjectFactory(factory.Factory):
    '''
    Package for the following command:

    `tds package add fake_package badf00d`
    by user 'fake_user'.
    '''
    FACTORY_FOR = p.Project

    name = 'fake_project'
    package_definitions = [ApplicationFactory(name="app1", path='/job/app1'),
                           ApplicationFactory(name="app2", path='/job/app2')]


    # delegate = _ProjectDelegate()
