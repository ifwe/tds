from mock import patch
import unittest

import tds.notifications.hipchat as hipchat

from tests.factories.utils.config import DeployConfigFactory
from tests.factories.model.deployment import DeploymentFactory

APP_CONFIG = DeployConfigFactory()


class TestHipChatNotifier(unittest.TestCase):

    class FakeResponse(object):

        def __init__(self, status_code=200):
            self.status_code = status_code

    def setUp(self):
        self.hipchat_config = APP_CONFIG['notifications']['hipchat']
        self.notifier = hipchat.HipchatNotifier(
            APP_CONFIG,
            self.hipchat_config
        )

    @patch('requests.post')
    def test_successful_notify(self, post):
        deployment = DeploymentFactory()
        post.return_value = self.FakeResponse()

        with patch.object(self.notifier, 'message_for_deployment') as mck_msg:
            mck_msg.return_value = dict(
                subject='fake_subj',
                body='fake_body',
            )
            self.notifier.notify(deployment)

        post.assert_called_with(
            'https://api.hipchat.com/v1/rooms/message',
            **dict(
                headers={
                    'Content-Length': '0'
                },
                proxies={
                    'https': 'http://proxy.example.com:443'
                },
                params={
                    'from': 'fake_user',
                    'auth_token': self.hipchat_config['token'],
                    'room_id': self.hipchat_config['rooms'][0],
                    'message': '<strong>{subj}</strong><br />{body}'.format(
                        subj='fake_subj',
                        body='fake_body'
                    )
                }
            )
        )

    @patch('requests.post')
    def test_failed_notify(self, post):
        deployment = DeploymentFactory()
        post.return_value = self.FakeResponse(404)

        with patch.object(self.notifier, 'message_for_deployment') as mck_msg:
            mck_msg.return_value = dict(
                subject='fake_subj',
                body='fake_body',
            )
            self.notifier.notify(deployment)

        post.assert_called_with(
            'https://api.hipchat.com/v1/rooms/message',
            **dict(
                headers={
                    'Content-Length': '0'
                },
                proxies={
                    'https': 'http://proxy.example.com:443'
                },
                params={
                    'from': 'fake_user',
                    'auth_token': self.hipchat_config['token'],
                    'room_id': self.hipchat_config['rooms'][0],
                    'message': '<strong>{subj}</strong><br />{body}'.format(
                        subj='fake_subj',
                        body='fake_body'
                    )
                }
            )
        )
        # TODO: This test should check for the logs for:
        # 'Notification to HipChat failed, status code is: %r', 404
