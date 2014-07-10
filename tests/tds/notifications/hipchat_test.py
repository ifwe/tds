from mock import patch, Mock
import unittest2

import tds.notifications.hipchat as hipchat

from tests.factories.utils.config import DeployConfigFactory
from tests.factories.model.deployment import DeploymentFactory

APP_CONFIG = DeployConfigFactory()


class TestHipchatNotifier(unittest2.TestCase):
    def setUp(self):
        self.project_rooms = ['fakeroom1', 'fakeroom2']

        project_class_mock = patch('tds.model.Project').start()
        hipchats = [Mock(room_name=r) for r in self.project_rooms]
        target = Mock(hipchats=hipchats)
        project_class_mock.get.return_value.targets = [target]

    def tearDown(self):
        patch.stopall()

    @patch('requests.api.request')
    def test_notify(self, request):
        h = hipchat.HipchatNotifier(
            APP_CONFIG,
            APP_CONFIG['notifications']['hipchat']
        )

        deployment = DeploymentFactory()
        with patch.object(h, 'message_for_deployment') as mock_message:
            mock_message.return_value = dict(
                subject='fake subj',
                body='fake body'
            )

            h.notify(deployment)

        token = APP_CONFIG['notifications']['hipchat']['token']
        rooms = APP_CONFIG['notifications']['hipchat']['rooms']
        rooms = rooms + self.project_rooms

        rooms_callargs = zip(
            rooms,
            request.call_args_list
        )

        for room, call_args in rooms_callargs:
            args, kwargs = call_args
            assert args == ('post', 'https://api.hipchat.com/v1/rooms/message')
            assert kwargs == {
                'data': None,
                'params': {
                    'auth_token': token,
                    'room_id': room,
                    'from': deployment.actor.name,
                    'message': (
                        '<strong>fake subj</strong><br />fake body'
                    ),
                },
                'headers': {'Content-Length': '0'},
                'proxies': h.proxies,
            }
