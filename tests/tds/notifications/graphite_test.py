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

from mock import patch
import unittest

import tds.notifications.graphite as graphite

from tests.factories.utils.config import DeployConfigFactory
from tests.factories.model.deployment import DeploymentFactory

APP_CONFIG = DeployConfigFactory()


class TestGraphiteNotifier(unittest.TestCase):
    def setUp(self):
        self.graphite_config = APP_CONFIG['notifications']['graphite']
        self.notifier = graphite.GraphiteNotifier(
            APP_CONFIG,
            self.graphite_config
        )

        raise NotImplementedError("needs to be converted to 'graphitesend'")
        self.graphite = patch('graphiteudp.GraphiteUDPClient').start()

    def tearDown(self):
        patch.stopall()

    def test_inactive_event(self):
        with patch.object(self.notifier, 'active_events', ()):
            self.notifier.notify(DeploymentFactory())

        self.assertFalse(self.graphite.called)

    def test_active_event(self):
        d = DeploymentFactory()
        self.notifier.notify(d)

        self.graphite.assert_called_with(**dict(
            (x, self.graphite_config[x]) for x in ('host', 'port', 'prefix')
        ))

        self.graphite.return_value.send.assert_called_with(
            d.package.name, 1
        )
