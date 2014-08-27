'''
Factories to create various tds.model.project.Project instances
'''
import factory
import tds.model.project as p


class ProjectFactory(factory.Factory):
    '''
    Package for the following command:

    `tds package add fake_package badf00d`
    by user 'fake_user'.
    '''
    FACTORY_FOR = p.Project

    name = 'fake_project'
