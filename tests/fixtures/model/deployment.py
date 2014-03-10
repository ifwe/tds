'''
Some pre-instantiated Deployment objects for tests.
'''
from tds.model import Deployment

__all__ = ['DEPLOYMENTS']

# TODO: these should all go in respective fixture modules.

ACTOR = dict(
    username='fake_user',
    automated=False
)

ACTIONS = dict(
    unvalidated=dict(command='unvalidated'),
    deploy_promote=dict(
        command='deploy',
        subcommand='promote',
    )
)

PROJECT = dict(
    name='fake_project'
)

PACKAGE = dict(
    name=PROJECT['name'],  # TODO: make different from project name
    version='badf00d'
)

TARGET = dict(
    environment='test',
    apptypes=['fake_apptype'],
)


def _make_deployment(
        actor=ACTOR.copy(),
        action=ACTIONS['deploy_promote'].copy(),
        project=PROJECT.copy(),
        package=PACKAGE.copy(),
        target=TARGET.copy()
):
    '''
    Construct a Deployment object, with a bunch of prefilled attribute values.
    '''

    return Deployment(
        actor=actor,
        action=action,
        project=project,
        package=package,
        target=target,
    )

DEPLOYMENTS = dict(
    deploy=dict(
        promote=_make_deployment()
    ),
    unvalidated=_make_deployment(action=ACTIONS['unvalidated'])
)
