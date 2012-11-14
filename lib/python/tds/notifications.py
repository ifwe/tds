import os
import smtplib

from email.mime.text import MIMEText

import json
import requests

import tds.utils

import tagopsdb.deploy.deploy as deploy


class Notifications(object):
    """Manage various notification mechanisms for deployments"""

    def __init__(self, project, user, apptypes):
        """Configure various parameters needed for notifications"""

        self.sender = user
        self.sender_addr = '%s@tagged.com' % user

        (self.enabled_methods, self.receiver_addr,
         self.hipchat_rooms, self.hipchat_token) = \
            tds.utils.verify_conf_file_section('deploy', 'notifications')

        # Query DB for any additional Hipchat rooms
        self.hipchat_rooms.extend(deploy.find_hipchat_rooms_for_app(project,
                                                                    apptypes))


    def send_email(self, msg_subject, msg_text):
        """Send an email notification for a given action"""

        msg = MIMEText(msg_text)

        msg['Subject'] = msg_subject
        msg['From'] = self.sender_addr
        msg['To'] = self.receiver_addr

        s = smtplib.SMTP('localhost')
        s.sendmail(self.sender, [ self.receiver_addr ], msg.as_string())
        s.quit()


    def send_hipchat(self, msg_subject, msg_text):
        """Send a HipChat message for a given action"""

        os.environ['HTTP_PROXY'] = 'http://10.15.11.132:80/'
        os.environ['HTTPS_PROXY'] = 'http://10.15.11.132:443/'

        for room in self.hipchat_rooms:
            payload = { 'auth_token' : self.hipchat_token,
                        'room_id' : room,
                        'from' : self.sender,
                        'message' : '<strong>%s</strong><br />%s'
                                    % (msg_subject, msg_text), }

            # Content-Length must be set in header due to bug in Python 2.6
            headers = { 'Content-Length' : '0' }

            r = requests.post('https://api.hipchat.com/v1/rooms/message',
                              params=payload, headers=headers)

            if r.status_code != requests.codes.ok:
                print 'Notification to Hipchat failed, status code is: %r' \
                      % r.status_code


    def send_notifications(self, msg_subject, msg_text):
        """Send out various enabled notifications for a given action"""

        for enabled in self.enabled_methods:
            getattr(self, 'send_%s' % enabled)(msg_subject, msg_text)
