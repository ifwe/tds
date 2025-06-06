# Copyright 2016 Ifwe Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'Stuff only needed for tds.scripts, and so far nowhere else'
from datetime import timedelta, datetime

import tagopsdb
import tagopsdb.deploy.deploy
import tds.notifications
import tds.model


class UnvalidatedDeploymentNotifier(tds.notifications.Notifications):
    'Bridge unvalidated tagopsdb AppDeployments and tds.Notifications'
    @staticmethod
    def convert_deployment(app_deployment):
        'Create a TDS Deployment instance for a tagopsdb AppDeployment'
        package = app_deployment.package

        return tds.model.DeployInfo(
            # XXX: How to get groups?
            actor=tds.model.Actor(name=app_deployment.user, groups=[]),
            action=dict(
                command='unvalidated',
            ),
            project=dict(
                # TODO: deployments should be for projects, not packages
                name=package.name,
            ),
            package=package,
            target=dict(
                environment=app_deployment.environment,
                apptypes=[app_deployment.target],
            ),
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
        tagopsdb.init(
            url=dict(
                username=dbconf['user'],
                password=dbconf['password'],
                host=dbconf['hostname'],
                database=dbconf['db_name'],
            ),
        )

    @staticmethod
    def get_all(environment):
        'Get all unvalidated deployments for `environment`'
        environment = \
            tds.model.Environment.find(env=environment)[0].environment

        return (
            tagopsdb.deploy.deploy.find_unvalidated_deployments(environment)
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
