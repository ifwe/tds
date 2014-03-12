import os
import requests
import tagopsdb.deploy.deploy as deploy

import logging
log = logging.getLogger('tds')

from .base import Notifications, Notifier


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
