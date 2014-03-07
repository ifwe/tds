from tds.model import Deployment

deployments = dict(
    deploy=dict(
        promote=Deployment(
            actor=dict(
                username='fake_user',
                automated=False
            ),
            action=dict(
                command='deploy',
                subcommand='promote',
            ),
            project=dict(
                name='fake_project'
            ),
            package=dict(
                name='fake_project',  # TODO: make different from project name
                version='badf00d'
            ),
            target=dict(
                environment='test',
                apptypes=['fake_apptype'],
            )
        ),
    ),
)
