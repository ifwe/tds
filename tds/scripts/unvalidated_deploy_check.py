'Notify about unvalidated deployments'
import sys

from datetime import timedelta, datetime
import tds.notifications
import tds.utils.config

import tagopsdb
import tds.model


class UnvalidatedDeploymentNotifier(tds.notifications.Notifications):
    'Bridge unvalidated tagopsdb AppDeployments and tds.Notifications'
    @staticmethod
    def convert_deployment(app_deployment):
        'Create a TDS Deployment instance for a tagopsdb AppDeployment'
        package = app_deployment.deployment.package

        return tds.model.Deployment(
            # XXX: How to get groups?
            actor=tds.model.Actor(name=app_deployment.user, groups=[]),
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
                environment=app_deployment.deployment.environment,
                apptypes=[app_deployment.application.app_type],
            )
        )


    def notify(self, app_deployments):
        for app_dep in app_deployments:
            deployment = self.convert_deployment(app_dep)
            super(UnvalidatedDeploymentNotifier, self).notify(deployment)


class TagopsdbDeploymentProvider(object):
    'Implementation of retrieving AppDeployments'
    def __init__(self, config):
        self.config = config

    def init(self):
        'Initialize database connection'
        dbconf = self.config['db']
        tagopsdb.init(dict(
            url=dict(
                username=dbconf['user'],
                password=dbconf['password'],
                host=dbconf['hostname'],
                database=dbconf['db_name'],
            ),
            pool_recycle=3600)
        )

    def get_all(self, environment):
        'Get all unvalidated deployments for `environment`'
        return tds.model.AppDeployment.find(
            environment=environment,
            needs_validation=True
        )


class ValidationMonitor(object):
    'Determine what deployments have been unvalidated for too long'
    def __init__(self, config, dep_provider):
        self.config = config
        self.deployment_provider = dep_provider

    @property
    def environment(self):
        'The environment to be monitored'
        return self.config['env.environment']

    @property
    def validation_grace_duration(self):
        'How long a deployment can go without being validated'
        return self.config['notifications.validation_time']

    def should_be_validated(self, app_deployment):
        'Determines if an AppDeployment should be validated or not'

        validation_grace_td = timedelta(seconds=self.validation_grace_duration)
        needs_validation_after = app_deployment.realized + validation_grace_td
        return datetime.now() >= needs_validation_after

    def get_deployments_requiring_validation(self):
        '''
        Find all instances of tagopsdb.AppDeployment in our environment that
        have not been validated
        '''
        return filter(
            self.should_be_validated,
            self.deployment_provider.get_all(self.environment)
        )


def main():
    'Load config, create ValidationMonitor instance, and process notifications'
    config = tds.utils.config.TDSDeployConfig()
    db_config = tds.utils.config.TDSDatabaseConfig('admin', 'tagopsdb')

    dep_provider = TagopsdbDeploymentProvider(db_config)
    vmon = ValidationMonitor(config, dep_provider)
    notifier = UnvalidatedDeploymentNotifier(config)

    dep_provider.init()
    notifier.notify(vmon.get_deployments_requiring_validation())

    return 0

if __name__ == '__main__':
    sys.exit(main())
