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

'''
Notifier and helpers for sending notifications via graphite
'''
import graphiteudp

from .base import Notifications, Notifier


@Notifications.add('graphite')
class GraphiteNotifier(Notifier):
    '''
    Send graphite notification
    '''
    active_events = (
        ('deploy', 'fix'),
        ('deploy', 'promote'),
        ('deploy', 'rollback')
    )

    def notify(self, deployment):
        event = (
            deployment.action.get('command'),
            deployment.action.get('subcommand')
        )
        if event not in self.active_events:
            return

        graphite = graphiteudp.GraphiteUDPClient(
            host=self.config['host'],
            port=self.config['port'],
            prefix=self.config['prefix']
        )

        graphite.send(deployment.package.name, 1)
