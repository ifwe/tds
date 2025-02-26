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

'''
Base class and functionality for notifications sent from TDS
'''
import logging

import tds.utils
import tds.model

log = logging.getLogger('tds')

__all__ = ['Notifications', 'Notifier']


class Notifications(object):
    """Manage various notification mechanisms for deployments"""

    _notifiers = None

    @classmethod
    def add(cls, name):
        '''
        Add a new notifier type
        '''
        def notifier_add(notifier_factory):
            'Takes a callable that will be used for the notifier'
            if cls._notifiers is None:
                cls._notifiers = {}

            cls._notifiers[name] = notifier_factory
            return notifier_factory

        return notifier_add

    @tds.utils.debug
    def __init__(self, config):
        """Configure various parameters needed for notifications"""

        self._config = config
        self.config = config.get('notifications', {})

        log.debug('Initializing for notifications')

        self.enabled_methods = self.config.get('enabled_methods', [])
        self.validation_time = self.config.get('validation_time', 30 * 60)

        log.log(5, 'Enabled notification methods: %s',
                ', '.join(self.enabled_methods))
        log.log(5, 'Validation timeout (in seconds): %s',
                self.validation_time)

    @tds.utils.debug
    def notify(self, deployment):
        """Send out various enabled notifications for a given action"""

        log.debug(
            "Sending notification(s) for package: %s, version: %s" % (
                deployment.package.name, deployment.package.version
            ),
        )
        notifiers = self._notifiers or {}

        for method in self.enabled_methods:
            notifier_factory = notifiers.get(method)
            notifier = notifier_factory(
                self._config,
                self.config.get(method, {})
            )
            notifier.notify(deployment)


class Notifier(object):
    '''
    Base class for a Notifier
    '''
    def __init__(self, app_config, config):
        self.app_config = app_config
        self.config = config

    def notify(self, deployment):
        'Send a notification'
        raise NotImplementedError

    def message_for_deployment(self, deployment):
        '''Return message object for the deployment. Dispatches
            on the deployment's action's "command" property, or uses the
            default method, "message_for_default".
        '''

        method_name = 'message_for_%s' % deployment.action['command']
        return getattr(self, method_name, self.message_for_default)(
            deployment
        )

    def message_for_default(self, deployment):
        '''Return message object for the deployment. Dispatches
            on the deployment's action's "subcommand" property, or uses
            the default method, "message_for_default_default".
        '''
        method_name = 'message_for_default_%s' \
            % deployment.action['subcommand']
        return getattr(
            self, method_name, self.message_for_default_default
        )(deployment)

    @staticmethod
    def message_for_unvalidated(deployment):
        'Returns the message for an unvalidated deployment'
        package = deployment.package
        subject = (
            'ATTENTION: %s in %s for %s app tier needs validation!' % (
                package.name,
                deployment.target['environment'],
                ','.join(x.name for x in deployment.target['apptypes'])
            )
        )
        body = (
            "Version %s of package %s in %s app tier\n"
            "has not been validated. Please validate it.\n"
            "Without this, Puppet cannot manage the tier correctly." % (
                package.version,
                package.name,
                ', '.join(x.name for x in deployment.target['apptypes']),
            )
        )

        return dict(subject=subject, body=body)

    def message_for_default_default(self, deployment):
        'Default message that will be used unless another handler is found'
        log.debug('Creating information for notifications')

        package = deployment.package

        # Determine version
        version = package.version

        log.log(5, 'Application version is: %s', version)

        dep_type = deployment.action['subcommand'].capitalize()

        if deployment.target.get('hosts', None):
            dest_type = 'hosts'
            destinations = ', '.join(
                sorted(x.name for x in deployment.target['hosts'])
            )
        elif deployment.target.get('apptypes', None):
            dest_type = 'app tier(s)'
            destinations = ', '.join(
                sorted(x.name for x in deployment.target['apptypes'])
            )
        else:
            dest_type = 'app tier(s)'

            targets = deployment.target.get('apptypes', [])
            destinations = ', '.join(sorted(x.name for x in targets))

        log.log(5, 'Destination type is: %s', dest_type)
        log.log(5, 'Destinations are: %s', destinations)

        msg_subject = '%s of version %s of %s on %s %s in %s' \
                      % (dep_type, version, package.name,
                         dest_type, destinations,
                         self.app_config['env.environment'])
        msg_args = (
            deployment.actor.name, deployment.action['command'],
            deployment.action['subcommand'], dest_type,
            self.app_config['env.environment'], destinations
        )
        msg_text = '%s performed a "tds %s %s" for the following %s ' \
                   'in %s:\n    %s' % msg_args

        return dict(subject=msg_subject, body=msg_text)

    def factors_for_deployment(self, deployment):
        """
        Collect basic info about a deployment and return a dict of strings. If
        the deployment lacks a subcommand, though, then this is presumed to not
        be an actual deployment, but rather something else which is using the
        same notification framework; in that case, return None.
        """
        if 'subcommand' not in deployment.action:
            log.debug('This seems to be a notification but not an actual deployment.')
            return None

        log.debug('Collecting factors for deployment')

        dep_type = deployment.action['subcommand'].capitalize()

        package = deployment.package

        # Determine version
        version = package.version

        package_name = package.name

        if deployment.target.get('hosts', None):
            app = False
            destinations = ', '.join(
                sorted(x.name for x in deployment.target['hosts'])
            )
        elif deployment.target.get('apptypes', None):
            app = True
            destinations = ', '.join(
                sorted(x.name for x in deployment.target['apptypes'])
            )
        else:
            app = True
            targets = deployment.target.get('apptypes', [])
            destinations = ', '.join(sorted(x.name for x in targets))

        env = self.app_config['env.environment']

        deployer = deployment.actor.name

        return dict(
            app=app,
            dep_type=dep_type,
            deployer=deployer,
            destinations=destinations,
            env=env,
            package_name=package_name,
            version=version,
        )
