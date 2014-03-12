import logging
import os

import smtplib
from email.mime.text import MIMEText

import requests

import graphiteudp

import tds.utils
import tagopsdb.deploy.deploy as deploy
import tagopsdb.deploy.repo as repo


log = logging.getLogger('tds')


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
                deployment.package['version'],
                deployment.package['name'],
                ', '.join(deployment.target['apptypes']),
            )
        )

        return dict(subject=subject, body=body)

    def message_for_default_default(self, deployment):

        log.debug('Creating information for notifications')

        # Determine version
        version = deployment.package['version']

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
            app_pkgs = repo.find_app_packages_mapping(
                deployment.project['name']
            )
            destinations = ', '.join(x.app_type for x in app_pkgs)

        log.debug(5, 'Destination type is: %s', dest_type)
        log.debug(5, 'Destinations are: %s', destinations)

        msg_subject = '%s of version %s of %s on %s %s in %s' \
                      % (dep_type, version, deployment.package['name'],
                         dest_type, destinations,
                         self.app_config['env.environment'])
        msg_args = (
            deployment.actor['username'], deployment.action['command'],
            deployment.action['subcommand'], dest_type,
            self.app_config['env.environment'], destinations
        )
        msg_text = '%s performed a "tds %s %s" for the following %s ' \
                   'in %s:\n    %s' % msg_args

        return dict(subject=msg_subject, body=msg_text)


@Notifications.add('hipchat')
class HipchatNotifier(Notifier):
    def __init__(self, app_config, config):
        super(HipchatNotifier, self).__init__(app_config, config)
        self.token = config['token']
        self.rooms = config['rooms']

    def notify(self, deployment):
        """Send a HipChat message for a given action"""

        message = self.message_for_deployment(deployment)

        # Query DB for any additional HipChat rooms
        log.debug('Looking for additional HipChat rooms to be notified')
        extra_rooms = deploy.find_hipchat_rooms_for_app(
            deployment.project['name'],
            deployment.target['apptypes'],
        )
        log.debug(5, 'HipChat rooms to notify: %s',
                  ', '.join(self.rooms))
        log.debug(5, 'HipChat token: %s', self.token)

        log.debug('Sending HipChat notification(s)')

        os.environ['HTTP_PROXY'] = 'http://10.15.11.132:80/'
        os.environ['HTTPS_PROXY'] = 'http://10.15.11.132:443/'

        for room in self.rooms + extra_rooms:
            payload = {
                'auth_token': self.token,
                'room_id': room,
                'from': deployment.actor['username'],
                'message': ('<strong>%(subject)s</strong><br />%(body)s'
                            % message),
            }

            # Content-Length must be set in header due to bug in Python 2.6
            headers = {'Content-Length': '0'}

            r = requests.post('https://api.hipchat.com/v1/rooms/message',
                              params=payload, headers=headers)

            if r.status_code != requests.codes.ok:
                log.error('Notification to HipChat failed, status code '
                          'is: %r', r.status_code)


@Notifications.add('email')
class EmailNotifier(Notifier):
    def __init__(self, app_config, config):
        super(EmailNotifier, self).__init__(app_config, config)
        self.receiver = config.get('receiver')

    def notify(self, deployment):
        """Send an email notification for a given action"""

        log.debug('Sending email notification(s)')

        message = self.message_for_deployment(deployment)
        sender_addr = '%s@tagged.com' % deployment.actor['username']
        receiver_emails = [sender_addr, self.receiver]

        log.debug(5, 'Receiver\'s email address: %s', self.receiver)
        log.debug(5, 'Sender\'s email address is: %s', sender_addr)

        msg = MIMEText(message['body'])

        msg['Subject'] = '[TDS] %s' % message['subject']
        msg['From'] = sender_addr
        msg['To'] = ', '.join(receiver_emails)

        s = smtplib.SMTP('localhost')
        s.sendmail(
            deployment.actor['username'],
            receiver_emails,
            msg.as_string()
        )
        s.quit()


@Notifications.add('graphite')
class GraphiteNotifier(Notifier):
    active_events = (
        ('config', 'push'),
        ('config', 'repush'),
        ('config', 'revert'),
        ('deploy', 'promote'),
        ('deploy', 'redeploy'),
        ('deploy', 'rollback')
    )

    def notify(self, deployment):
        event = (
            deployment.action.get('command'),
            deployment.action.get('subcommand')
        )
        if event not in self.active_events:
            return

        graphite = graphiteudp.GraphiteUDPClient(
            host=self.config['host'],
            port=self.config['port'],
            prefix=self.config['prefix']
        )

        graphite.send(deployment.package['name'], 1)
