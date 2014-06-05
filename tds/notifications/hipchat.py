'''
Support for hipchat notifications
'''
import requests

import logging
log = logging.getLogger('tds')

import tds.model
from .base import Notifications, Notifier


@Notifications.add('hipchat')
class HipchatNotifier(Notifier):
    '''
    Notifier for hipchat
    '''
    def __init__(self, app_config, config):
        super(HipchatNotifier, self).__init__(app_config, config)
        self.token = config['token']
        self.rooms = config['rooms']

    @property
    def proxies(self):
        'Determine proxies for request'
        proxies = {}
        config_proxies = self.app_config.get('proxy', {})
        for proto in ('http', 'https'):
            if proto in config_proxies:
                proxies[proto] = config_proxies[proto]

        return proxies

    def notify(self, deployment):
        """Send a HipChat message for a given action"""

        message = self.message_for_deployment(deployment)

        # Query DB for any additional HipChat rooms
        log.debug('Looking for additional HipChat rooms to be notified')
        project = tds.model.Project.get(name=deployment.project['name'])
        hipchats = sum((t.hipchats for t in project.targets), [])
        extra_rooms = [x.room_name for x in hipchats]

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
        'Perform the necessary http request to send a hipchat message'
        payload = {
            'auth_token': self.token,
            'room_id': room,
            'from': user,
            'message': message,
        }

        # Content-Length must be set in header due to bug in Python 2.6
        headers = {'Content-Length': '0'}

        resp = requests.post(
            'https://api.hipchat.com/v1/rooms/message',
            params=payload,
            headers=headers,
            proxies=self.proxies
        )

        if resp.status_code != requests.codes.ok:
            log.error('Notification to HipChat failed, status code '
                      'is: %r', resp.status_code)
