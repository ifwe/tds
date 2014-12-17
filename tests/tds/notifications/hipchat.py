from mock import patch
import unittest

import tds.notifications.hipchat as hipchat

from tests.factories.utils.config import DeployConfigFactory
from tests.factories.model.deploy import DeploymentFactory

APP_CONFIG = DeployConfigFactory()


class TestHipChatNotifier(unittest.TestCase):

    def setUp(self):
        self.hipchat_config = APP_CONFIG['notifications']['hipchat']
        self.notifier = hipchat.HipchatNotifier(
            APP_CONFIG,
            self.hipchat_config
        )

        self.requests = patch('requests.post')

    def test_successful_notify(self):
        receiver = APP_CONFIG['notifications']['hipchat']['recevier']
        deployment = DeploymentFactory()

        with patch.object(e, 'message_for_deployment') as mock_message:
            mock_message.return_value = dict(
                subject='fake_subj',
                body='fake_body',
            )

            self.notifier.notify(deployment)

        self.requests.assert_called_with(**dict(
            ()
        ))
        assert False
