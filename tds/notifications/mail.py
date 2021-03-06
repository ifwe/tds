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

"""Notifier and helpers for sending notifications via email"""

import logging
import smtplib

from email.mime.text import MIMEText

from .base import Notifications, Notifier

log = logging.getLogger('tds')


@Notifications.add('email')
class EmailNotifier(Notifier):
    """Send email notification via SMTP"""

    def __init__(self, app_config, config):
        super(EmailNotifier, self).__init__(app_config, config)
        self.receiver = config.get('receiver')
        self.domain = config.get('sender_domain')
        self.port = config.get('port', 25)

    def notify(self, deployment):
        """Send an email notification for a given action"""

        log.debug('Sending email notification(s)')

        message = self.message_for_deployment(deployment)
        sender_addr = '%s@%s' % (deployment.actor.name, self.domain)
        receiver_emails = [sender_addr, self.receiver]

        log.log(5, 'Receiver\'s email address: %s', self.receiver)
        log.log(5, 'Sender\'s email address is: %s', sender_addr)

        msg = MIMEText(message['body'])

        msg['Subject'] = '[TDS] %s' % message['subject']
        msg['From'] = sender_addr
        msg['To'] = ', '.join(receiver_emails)

        smtp = smtplib.SMTP('localhost', self.port)
        try:
            smtp.sendmail(
                deployment.actor.name,
                receiver_emails,
                msg.as_string()
            )
        except smtplib.SMTPException as exc:
            log.error('Mail server failure: %s', exc)
        finally:
            smtp.quit()
