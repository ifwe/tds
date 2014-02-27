import logging
import os
import smtplib

from email.mime.text import MIMEText

import requests

import tds.utils
import tagopsdb.deploy.deploy as deploy


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
    def __init__(self, project, user, apptypes):
        """Configure various parameters needed for notifications"""

        self.config = tds.utils.config.TDSDeployConfig().get('notifications')

        # TODO: get these out of here and make part of the params to send()
        self.sender = user
        self.project = project
        self.apptypes = apptypes

        log.debug('Initializing for notifications')

        self.enabled_methods = self.config.get('enabled_methods', [])
        self.validation_time = self.config.get('validation_time', 30 * 60)

        log.debug(5, 'Enabled notification methods: %s',
                  ', '.join(self.enabled_methods))
        log.debug(5, 'Validation timeout (in seconds): %s',
                  self.validation_time)

    @tds.utils.debug
    def send_notifications(self, msg_subject, msg_text):
        """Send out various enabled notifications for a given action"""

        log.debug('Sending out enabled notifications')
        if self._notifiers is None:
            return

        for method in self.enabled_methods:
            notifier_factory = self._notifiers.get(method)
            notifier = notifier_factory(self.config.get(method, {}))
            notifier.send(
                self.sender,
                self.project,
                self.apptypes,
                msg_subject,
                msg_text
            )


class Notifier(object):
    def __init__(self, config):
        pass

    def send(self, sender, project, apptypes, msg_subject, msg_text):
        raise NotImplementedError


@Notifications.add('hipchat')
class HipchatNotifier(Notifier):
    def __init__(self, config):
        self.token = config['token']
        self.rooms = config['rooms']

    @tds.utils.debug
    def send(self, sender, project, apptypes, msg_subject, msg_text):
        """Send a HipChat message for a given action"""

        # Query DB for any additional HipChat rooms
        log.debug('Looking for additional HipChat rooms to be notified')
        extra_rooms = deploy.find_hipchat_rooms_for_app(project, apptypes)
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
                'from': sender,
                'message': ('<strong>%s</strong><br />%s'
                            % (msg_subject, msg_text)),
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
    def __init__(self, config):
        self.receiver = config.get('receiver')

    @tds.utils.debug
    def send(self, sender, project, apptypes, msg_subject, msg_text):
        """Send an email notification for a given action"""

        log.debug('Sending email notification(s)')

        sender_addr = '%s@tagged.com' % sender
        receiver_emails = [sender_addr, self.receiver]

        log.debug(5, 'Receiver\'s email address: %s', self.receiver)
        log.debug(5, 'Sender\'s email address is: %s', sender_addr)

        msg = MIMEText(msg_text)

        msg['Subject'] = '[TDS] %s' % msg_subject
        msg['From'] = sender_addr
        msg['To'] = ', '.join(receiver_emails)

        s = smtplib.SMTP('localhost')
        s.sendmail(sender, receiver_emails, msg.as_string())
        s.quit()
