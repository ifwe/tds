import sys

import tagopsdb.deploy.deploy as deploy
import tds.notifications
import tds.utils.config
from tds.model import Deployment, LocalActor

import tagopsdb
envs = {'dev': 'development',
        'stage': 'staging',
        'prod': 'production', }


def main(*args):
    config = tds.utils.config.TDSDeployConfig()
    dbconfig = tds.utils.config.TDSDatabaseConfig('admin')

    tagopsdb.init(dict(
        url=dict(
            username=dbconfig['db.user'],
            password=dbconfig['db.password'],
            host=dbconfig['db.hostname'],
            database=dbconfig['db.db_name'],
        ),
        pool_recycle=3600)
    )

    env = config['env.environment']
    validation_time = config['notifications.validation_time']

    not_validated = deploy.find_unvalidated_versions(
        validation_time, envs[env]
    )

    for entry in not_validated:
        (pkg_name, version, revision, app_type, environment, realized,
         user, status) = entry

        deployment = Deployment(
            actor=LocalActor(),
            action=dict(
                command='unvalidated',
            ),
            project=dict(
                name=pkg_name,
            ),
            package=dict(
                name=pkg_name,
                version=version,
            ),
            target=dict(
                environment=environment,
                apptypes=[app_type],
            )
        )

        tds.notifications.Notifications(config).notify(deployment)

    return 0

if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
