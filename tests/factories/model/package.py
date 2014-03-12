'''
Factories to create various tds.model.deployment.Deployment instances
'''
import factory
import tds.model.package as p


class PackageFactory(factory.Factory):
    '''
    Package for the following command:

    `tds package add fake_package badf00d`
    by user 'fake_user'.
    '''
    FACTORY_FOR = p.Package

    package = dict(
        name='fake_package',
        version='badf00d',
    )
