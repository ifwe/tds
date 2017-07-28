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
Support for Signalfx notifications
"""

import json
import requests

import logging
log = logging.getLogger('tds')

from .base import Notifications, Notifier


@Notifications.add('signalfx')
class SignalfxNotifier(Notifier):
    """
    Notifier for Signalfx.
    """

    def __init__(self, app_config, config):
        """
        Extract and set config variables.
        """
        super(SignalfxNotifier, self).__init__(app_config, config)
        self.signalfx_url = config['url']
        self.signalfx_key = config['key']

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
        Send a Signalfx notification for a given action.
        """
        log.debug("Seding Signalfx notification")
        factors = self.factors_for_deployment(deployment)
        if factors['app']:
            applications = factors['destinations']
            nodes = ''
        else:
            applications = ''
            nodes = factors['destinations']

        payload = {
            "eventType": "software change",
            "dimensions": {
                "application": applications,
                "brand": "tagged",
                "company_code": "ifwe",
                "env": factors['env'],
                "node": nodes,
            },
            "properties": {
                "artifact_name": factors['package_name'],
                "artifact_type": "rpm",
                "changed_by": factors['deployer'],
                "deploy_type": factors['dep_type'],
                "release_method": "tds",
                "release_version": factors['version'],
            },
        }
        headers = {
            'Content-type': 'application/json',
            'X-SF-TOKEN': self.signalfx_key,
        }

        try:
            resp = requests.post(
                self.signalfx_url,
                headers=headers,
                data=json.dumps([payload]),
                proxies=self.proxies,
            )
            if resp.status_code != requests.codes.ok:
                log.error("Deployment successful, but failed to send Signalfx "
                          "notification. Got status code {code}.".format(
                            code=resp.status_code,
                          ))
        except requests.RequestException as exc:
            log.error(
                "Deployment successful, but failed to send Signalfx notification. "
                "Got exception: {exc}".format(exc=exc)
            )
