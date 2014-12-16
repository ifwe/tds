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
