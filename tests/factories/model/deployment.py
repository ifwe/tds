'''
Factories to create various tds.model.deployment.Deployment instances
'''
import datetime
import factory
import tds.model.deploy_info as deploy_info
import tds.model.deployment as deployment

from .actor import ActorFactory
from .package import PackageFactory
from .project import ProjectFactory
from .deploy_target import AppTargetFactory, HostTargetFactory, HipchatFactory


class DeploymentFactory(factory.Factory):
    '''
    Deployment for the following command:

    `tds deploy promote fake_project --apptype=fake_apptype`
    by user 'fake_user' in the 'test' tier.
    '''
    FACTORY_FOR = deploy_info.DeployInfo

    actor = factory.SubFactory(ActorFactory)
    package = factory.SubFactory(PackageFactory)
    project = factory.SubFactory(ProjectFactory)

    action = dict(
        command='deploy',
        subcommand='promote',
    )

    target = dict(
        env='dev',
        apptypes=[AppTargetFactory(
            name='fake_apptype',
            hipchats=[HipchatFactory(room_name="fakeroom")]
        )],
        hosts=None,
    )


class HostDeploymentFactory(DeploymentFactory):
    '''
    Deployment for the following command:

    `tds deploy promote fake_project --hosts=whatever.example.com`
    by user 'fake_user' in the 'test' tier.
    '''

    target = dict(
        env='test',
        hosts=[HostTargetFactory(name='whatever.example.com')]
    )


class AllApptypesDeploymentFactory(DeploymentFactory):
    '''
    Deployment for the following command:

    `tds deploy promote fake_project --all-apptypes`
    by user 'fake_user' in the 'test' tier.
    '''

    target = dict(
        env='test',
        apptypes=[
            AppTargetFactory(name='fake_apptype1'),
            AppTargetFactory(name='fake_apptype2')
        ]
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
    """
    Factory for creating app deployments.
    """
    FACTORY_FOR = deployment.AppDeployment
    FACTORY_STRATEGY = factory.STUB_STRATEGY

    environment = 'test'
    status = 'complete'

    needs_validation = False
    realized = factory.LazyAttribute(lambda o: datetime.datetime.utcnow())
