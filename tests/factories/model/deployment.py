'''
Factories to create various tds.model.deployment.Deployment instances
'''
import factory
import tds.model.deployment as d

from .package import PackageFactory


class DeploymentFactory(factory.Factory):
    '''
    Deployment for the following command:

    `tds deploy promote fake_project --apptype=fake_apptype`
    by user 'fake_user' in the 'test' tier.
    '''
    FACTORY_FOR = d.Deployment

    actor = dict(
        username='fake_user',
        automated=False,
    )

    action = dict(
        command='deploy',
        subcommand='promote',
    )

    project = factory.LazyAttribute(lambda d: dict(name=d.package.name))

    package = factory.SubFactory(PackageFactory)

    target = dict(
        environment='test',
        apptypes=['fake_apptype'],
    )


class UnvalidatedDeploymentFactory(DeploymentFactory):
    '''
    Deployment object generated when this command:

    `tds deploy promote fake_project --apptype=fake_apptype`
    by user 'fake_user' in the 'test' tier

    has not been validated and the unvalidated_deploy_check.py script is run
    '''
    action = dict(command='unvalidated')


class PackageAddFactory(DeploymentFactory):
    '''
    Package for the following command:

    `tds package add fake_package badf00d`
    by user 'fake_user'.
    '''
    action = dict(
        command='package',
        subcommand='add',
    )

    target = None
