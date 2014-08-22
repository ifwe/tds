'''
Notifier and helpers for sending notifications via email
'''
import logging
log = logging.getLogger('tds')

import smtplib
from email.mime.text import MIMEText

from .base import Notifications, Notifier


@Notifications.add('email')
class EmailNotifier(Notifier):
    '''
    Send email notification via smtp
    '''
    def __init__(self, app_config, config):
        super(EmailNotifier, self).__init__(app_config, config)
        self.receiver = config.get('receiver')

    def notify(self, deployment):
        """Send an email notification for a given action"""

        log.debug('Sending email notification(s)')

        message = self.message_for_deployment(deployment)
        sender_addr = '%s@tagged.com' % deployment.actor.name
        receiver_emails = [sender_addr, self.receiver]

        log.log(5, 'Receiver\'s email address: %s', self.receiver)
        log.log(5, 'Sender\'s email address is: %s', sender_addr)

        msg = MIMEText(message['body'])

        msg['Subject'] = '[TDS] %s' % message['subject']
        msg['From'] = sender_addr
        msg['To'] = ', '.join(receiver_emails)

        smtp = smtplib.SMTP('localhost')
        smtp.sendmail(
            deployment.actor.name,
            receiver_emails,
            msg.as_string()
        )
        smtp.quit()
