import sys

from datetime import timedelta, datetime
import tds.notifications
import tds.utils.config

import tagopsdb
import tds.model


def should_be_validated(dep, validation_grace_duration):
    'Determines if an AppDeployment should be validated or not'
    validation_grace_td = timedelta(seconds=validation_grace_duration)
    needs_validation_after = dep.realized + validation_grace_td
    return datetime.now() >= needs_validation_after


def init_database(config):
    'Connect tagopsdb lib to database'
    tagopsdb.init(dict(
        url=dict(
            username=config['user'],
            password=config['password'],
            host=config['hostname'],
            database=config['db_name'],
        ),
        pool_recycle=3600)
    )


def deployment_for_entry(entry):
    package = entry.deployment.package

    return tds.model.Deployment(
        actor=tds.model.LocalActor(),
        action=dict(
            command='unvalidated',
        ),
        project=dict(
            # TODO: deployments should be for projects, not packages
            name=package.name,
        ),
        package=dict(
            name=package.name,
            version=package.version,
        ),
        target=dict(
            environment=entry.deployment.environment,
            apptypes=[entry.application.app_type],
        )
    )


def notify_for_entry(config, entry):
    deployment = deployment_for_entry(entry)
    tds.notifications.Notifications(config).notify(deployment)


def main():
    config = tds.utils.config.TDSDeployConfig()
    dbconfig = tds.utils.config.TDSDatabaseConfig('admin', 'tagopsdb')

    init_database(dbconfig['db'])
    validation_grace_duration = config['notifications.validation_time']

    needs_validation = [
        x for x in tds.model.AppDeployment.find(
            environment=config['env.environment'],
            needs_validation=True
        ) if should_be_validated(x, validation_grace_duration)
    ]

    for entry in needs_validation:
        notify_for_entry(config, entry)

    return 0

if __name__ == '__main__':
    sys.exit(main())
