import logging
log = logging.getLogger('tds')

import tds.utils
import tds.model


class Notifications(object):
    """Manage various notification mechanisms for deployments"""

    _notifiers = None

    @classmethod
    def add(cls, name):
        def notifier_add(notifier_factory):
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

        log.debug(5, 'Enabled notification methods: %s',
                  ', '.join(self.enabled_methods))
        log.debug(5, 'Validation timeout (in seconds): %s',
                  self.validation_time)

    @tds.utils.debug
    def notify(self, deployment):
        """Send out various enabled notifications for a given action"""

        log.debug('Sending out enabled notifications')
        notifiers = self._notifiers or {}

        for method in self.enabled_methods:
            notifier_factory = notifiers.get(method)
            notifier = notifier_factory(
                self._config,
                self.config.get(method, {})
            )
            notifier.notify(deployment)


class Notifier(object):
    def __init__(self, app_config, config):
        self.app_config = app_config
        self.config = config

    def notify(self, deployment):
        raise NotImplementedError

    def message_for_deployment(self, deployment):
        '''Return message object for the deployment. Dispatches
            on the deployment's action's "command" property, or uses the
            default method, "message_for_default".
        '''

        method_name = 'message_for_%s' % deployment.action['command']
        return getattr(self, method_name, self.message_for_default)(deployment)

    def message_for_default(self, d):
        '''Return message object for the deployment. Dispatches
            on the deployment's action's "subcommand" property, or uses
            the default method, "message_for_default_default".
        '''
        method_name = 'message_for_default_%s' % d.action['subcommand']
        return getattr(self, method_name, self.message_for_default_default)(d)

    def message_for_unvalidated(self, deployment):
        subject = (
            'ATTENTION: %s in %s for %s app tier needs validation!' % (
                deployment.project['name'],
                deployment.target['environment'],
                ','.join(deployment.target['apptypes'])
            )
        )
        body = (
            'Version %s of package %s in %s app tier\n'
            'has not been validated. Please validate it.\n'
            'Without this, Puppet cannot manage the tier correctly.' % (
                deployment.package.version,
                deployment.package.name,
                ', '.join(deployment.target['apptypes']),
            )
        )

        return dict(subject=subject, body=body)

    def message_for_default_default(self, deployment):

        log.debug('Creating information for notifications')

        # Determine version
        version = deployment.package.version

        log.debug(5, 'Application version is: %s', version)

        dep_type = deployment.action['subcommand'].capitalize()

        if deployment.target.get('hosts', None):
            dest_type = 'hosts'
            destinations = ', '.join(deployment.target['hosts'])
        elif deployment.target.get('apptypes', None):
            dest_type = 'app tier(s)'
            destinations = ', '.join(deployment.target['apptypes'])
        else:
            dest_type = 'app tier(s)'

            targets = tds.model.Project.get(name=deployment.project['name']).targets
            destinations = ', '.join(x.app_type for x in targets)

        log.debug(5, 'Destination type is: %s', dest_type)
        log.debug(5, 'Destinations are: %s', destinations)

        msg_subject = '%s of version %s of %s on %s %s in %s' \
                      % (dep_type, version, deployment.package.name,
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
