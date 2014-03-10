import factory
import tds.model.deployment as d


class DeploymentFactory(factory.Factory):
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
    action = dict(command='unvalidated')
