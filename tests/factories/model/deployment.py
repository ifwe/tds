'''
Factories to create various tds.model.deployment.Deployment instances
'''
import factory
import tds.model.deployment as d


class DeploymentFactory(factory.Factory):
    '''
    Deployment for the following command:

    `tds deploy promote fake_project --apptype=fake_apptype`
    by user 'fake_user' in the 'test' tier.
    '''
    FACTORY_FOR = d.Deployment

    actor = dict(
        username='fake_user',
        automated=False
    )

    action = dict(
        command='deploy',
        subcommand='promote',
    )

    project = dict(
        name='fake_project'
    )

    package = dict(
        name=project['name'],
        version='badf00d'
    )

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
