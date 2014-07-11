'''
Factories to create various tds.model.deployment.Deployment instances
'''
import datetime
import factory
import tds.model.deployment as d

from .actor import ActorFactory
from .package import PackageFactory


class DeploymentFactory(factory.Factory):
    '''
    Deployment for the following command:

    `tds deploy promote fake_project --apptype=fake_apptype`
    by user 'fake_user' in the 'test' tier.
    '''
    FACTORY_FOR = d.Deployment

    actor = factory.SubFactory(ActorFactory)
    package = factory.SubFactory(PackageFactory)

    action = dict(
        command='deploy',
        subcommand='promote',
    )

    project = factory.LazyAttribute(lambda x: dict(name=x.package.name))

    target = dict(
        environment='test',
        apptypes=['fake_apptype'],
    )


class HostDeploymentFactory(DeploymentFactory):
    '''
    Deployment for the following command:

    `tds deploy promote fake_project --hosts=whatever.example.com`
    by user 'fake_user' in the 'test' tier.
    '''

    target = dict(
        environment='test',
        hosts=['whatever.example.com'],
    )


class AllApptypesDeploymentFactory(DeploymentFactory):
    '''
    Deployment for the following command:

    `tds deploy promote fake_project --all-apptypes`
    by user 'fake_user' in the 'test' tier.
    '''

    target = dict(
        environment='test',
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


class AppDeploymentFactory(factory.Factory):
    FACTORY_FOR = d.AppDeployment
    FACTORY_STRATEGY = factory.STUB_STRATEGY

    environment = 'test'
    status = 'complete'

    needs_validation = False
    realized = factory.LazyAttribute(lambda o: datetime.datetime.utcnow())
