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

"""
Support for hipchat notifications
"""
import requests

import logging
log = logging.getLogger('tds')

from .base import Notifications, Notifier


@Notifications.add('hipchat')
class HipchatNotifier(Notifier):
    """
    Notifier for hipchat
    """
    def __init__(self, app_config, config):
        super(HipchatNotifier, self).__init__(app_config, config)
        self.token = config['token']
        self.rooms = config['rooms']
        self.receiver = config.get(
            'receiver',
            'https://api.hipchat.com/v1/rooms/message'
        )

    @property
    def proxies(self):
        """Determine proxies for request."""
        proxies = {}
        config_proxies = self.app_config.get('proxy', {})
        for proto in ('http', 'https'):
            if proto in config_proxies:
                proxies[proto] = config_proxies[proto]

        return proxies

    def notify(self, deployment):
        """Send a HipChat message for a given action."""
        message = self.message_for_deployment(deployment)

        # Query DB for any additional HipChat rooms
        log.debug('Looking for additional HipChat rooms to be notified')

        extra_rooms = [
            hipchat.room_name
            for apptype in deployment.target['apptypes']
            for hipchat in apptype.hipchats
        ]

        log.log(5, 'HipChat rooms to notify: %s',
                ', '.join(self.rooms))
        log.log(5, 'HipChat token: %s', self.token)

        log.debug('Sending HipChat notification(s)')

        for room in self.rooms + extra_rooms:
            self.send_hipchat_message(
                room,
                deployment.actor.name,
                '<strong>%(subject)s</strong><br />%(body)s' % message
            )

    def send_hipchat_message(self, room, user, message):
        """Perform the necessary http request to send a hipchat message."""
        payload = {
            'auth_token': self.token,
            'room_id': room,
            'from': user,
            'message': message,
        }

        # Content-Length must be set in header due to bug in Python 2.6
        headers = {'Content-Length': '0'}

        try:
            resp = requests.post(
                self.receiver,
                params=payload,
                headers=headers,
                proxies=self.proxies
            )

            if resp.status_code != requests.codes.ok:
                log.error('Deployment was successful. However, notification to '
                          'HipChat failed, status code is: %r', resp.status_code)
        except requests.RequestException as exc:
            log.error(
                'Deployment was successful. However, notification to HipChat '
                'failed, message is: {exc}'.format(exc=exc)
            )
