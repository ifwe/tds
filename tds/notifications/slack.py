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
Support for Slack notifications
"""

import json
import requests

import logging

from .base import Notifications, Notifier

log = logging.getLogger('tds')


@Notifications.add('slack')
class SlackNotifier(Notifier):
    """
    Notifier for Slack.
    """

    def __init__(self, app_config, config):
        """
        Extract and set config variables.
        """
        super(SlackNotifier, self).__init__(app_config, config)
        self.slack_url = config['url']

    @property
    def proxies(self):
        """
        Determine proxies for request.
        """
        proxies = {}
        config_proxies = self.app_config.get('proxy', {})
        for proto in ('http', 'https'):
            if proto in config_proxies:
                proxies[proto] = config_proxies[proto]

        return proxies

    def notify(self, deployment):
        """
        Send a Slack notification for a given action.
        """
        log.debug("Sending Slack notification")

        message = self.message_for_deployment(deployment)
        payload = {
            "username": "tds",
            "icon-emoji": ":bell:",
            "text": "*{subject}*\n{body}".format(
                subject=message['subject'],
                body=message['body'],
            ),
        }

        headers = {'Content-type': 'application/json'}

        try:
            # Slack (or the proxy) can take up to a minute until responding
            # with an HTTP 504 "Gateway timeout". Limit this - we still send
            # emails
            resp = requests.post(
                self.slack_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=10.0,
                proxies=self.proxies,
            )
            if resp.status_code != requests.codes.ok:
                log.error("Deployment successful, but failed to send Slack "
                          "notification. Got status code {code}.".format(
                            code=resp.status_code,
                          ))
        except requests.RequestException as exc:
            log.error(
                "Deployment successful, but failed to send Slack notification. "
                "Got exception: {exc}".format(exc=exc)
            )
