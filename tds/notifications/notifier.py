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

    @tds.utils.debug
    def __init__(self, project, user, apptypes):
        """Configure various parameters needed for notifications"""

        config = tds.utils.config.TDSDeployConfig()

        log.debug('Initializing for notifications')

        self.sender = user
        self.sender_addr = '%s@tagged.com' % user
        log.debug(5, 'Sender\'s email address is: %s', self.sender_addr)

        self.__dict__.update(config['notifications'])
        log.debug(5, 'Enabled notification methods: %s',
                  ', '.join(self.enabled_methods))
        log.debug(5, 'Receiver\'s email address: %s', self.email_receiver)
        log.debug(5, 'Validation timeout (in seconds): %s',
                  self.validation_time)

        # Query DB for any additional HipChat rooms
        log.debug('Looking for additional HipChat rooms to be notified')
        self.hipchat_rooms = (
            self.hipchat_rooms +
            deploy.find_hipchat_rooms_for_app(project, apptypes)
        )
        log.debug(5, 'HipChat rooms to notify: %s',
                  ', '.join(self.hipchat_rooms))
        log.debug(5, 'HipChat token: %s', self.hipchat_token)

    @tds.utils.debug
    def send_email(self, msg_subject, msg_text):
        """Send an email notification for a given action"""

        log.debug('Sending email notification(s)')

        receiver_emails = [self.sender_addr, self.email_receiver]

        msg = MIMEText(msg_text)

        msg['Subject'] = '[TDS] %s' % msg_subject
        msg['From'] = self.sender_addr
        msg['To'] = ', '.join(receiver_emails)

        s = smtplib.SMTP('localhost')
        s.sendmail(self.sender, receiver_emails, msg.as_string())
        s.quit()

    @tds.utils.debug
    def send_hipchat(self, msg_subject, msg_text):
        """Send a HipChat message for a given action"""

        log.debug('Sending HipChat notification(s)')

        os.environ['HTTP_PROXY'] = 'http://10.15.11.132:80/'
        os.environ['HTTPS_PROXY'] = 'http://10.15.11.132:443/'

        for room in self.hipchat_rooms:
            payload = {
                'auth_token': self.hipchat_token,
                'room_id': room,
                'from': self.sender,
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

    @tds.utils.debug
    def send_notifications(self, msg_subject, msg_text):
        """Send out various enabled notifications for a given action"""

        log.debug('Sending out enabled notifications')

        for enabled in self.enabled_methods:
            getattr(self, 'send_%s' % enabled)(msg_subject, msg_text)
