from mock import patch, Mock
import unittest2

from tests.factories.utils.config import DeployConfigFactory
from tests.factories.model.deployment import (
    DeploymentFactory,
    UnvalidatedDeploymentFactory
)

import re
import email
import tds.notifications

APP_CONFIG = DeployConfigFactory()


class TestNotifications(unittest2.TestCase):

    def setUp(self):
        self.config = APP_CONFIG['notifications']

    def create_notification(self):
        return tds.notifications.Notifications(APP_CONFIG)

    def test_constructor(self):
        n = self.create_notification()

        assert n.config == self.config
        assert n.enabled_methods == self.config['enabled_methods']
        assert n.validation_time == self.config['validation_time']

    @patch('tds.notifications.notifier.EmailNotifier', autospec=True)
    @patch('tds.notifications.notifier.HipchatNotifier', autospec=True)
    def test_send_notifications(self, *notifiers):
        n = self.create_notification()

        notifiers = {
            'email': Mock(spec=tds.notifications.EmailNotifier),
            'hipchat': Mock(spec=tds.notifications.HipchatNotifier)
        }

        deployment = DeploymentFactory()
        with patch.object(n, '_notifiers', notifiers):
            n.notify(deployment)

            for mock in notifiers.values():
                assert mock.return_value.notify.called_with(deployment)


class TestNotifierClass(unittest2.TestCase):
    def test_send(self):
        n = tds.notifications.Notifier({}, {})
        self.assertRaises(
            NotImplementedError,
            n.notify,
            deployment=object()
        )

    def test_message_for_deploy_promote(self):
        n = tds.notifications.Notifier(
            APP_CONFIG,
            APP_CONFIG['notifications']
        )
        message = n.message_for_deployment(DeploymentFactory())

        assert isinstance(message['subject'], basestring)
        assert isinstance(message['body'], basestring)

        # are these assertions really necessary?
        assert message['subject'] == (
            'Promote of version badf00d of fake_project on app tier(s)'
            ' fake_apptype in fakedev'
        )
        assert message['body'] == (
            'fake_user performed a "tds deploy promote" for the following app '
            'tier(s) in fakedev:\n'
            '    fake_apptype'
        )

    def test_message_for_unvalidated(self):
        n = tds.notifications.Notifier(
            APP_CONFIG,
            APP_CONFIG['notifications'],
        )

        message = n.message_for_deployment(
            UnvalidatedDeploymentFactory()
        )
        assert isinstance(message['subject'], basestring)
        assert isinstance(message['body'], basestring)
        # do we want to assert any more here?


class TestEmailNotifier(unittest2.TestCase):
    @patch('smtplib.SMTP')
    def test_notify(self, SMTP):
        e = tds.notifications.EmailNotifier(
            APP_CONFIG,
            APP_CONFIG['notifications']['email']
        )

        receiver = APP_CONFIG['notifications']['email']['receiver']
        deployment = DeploymentFactory()

        with patch.object(e, 'message_for_deployment') as mock_message:
            mock_message.return_value = dict(
                subject='fake subj',
                body='fake body'
            )

            e.notify(deployment)

        SMTP.assert_called_with('localhost')
        (sender, recvrs, content), _kw = SMTP.return_value.sendmail.call_args
        assert sender == deployment.actor['username']
        self.assertItemsEqual(
            recvrs,
            [deployment.actor['username']+'@tagged.com',
             receiver]
        )

        unfold_header = lambda s: re.sub(r'\n(?:[ \t]+)', r' ', s)

        msg = email.message_from_string(content)
        username = deployment.actor['username']
        sender_email = username+'@tagged.com'
        ctype = 'text/plain; charset="us-ascii"'
        assert unfold_header(msg.get('content-type')) == ctype
        assert unfold_header(msg.get('subject')) == '[TDS] fake subj'
        assert unfold_header(msg.get('from')) == sender_email
        self.assertItemsEqual(
            msg.get('to').split(', '),
            [sender_email, receiver]
        )
        assert msg.get_payload() == 'fake body'

        assert SMTP.return_value.quit.called


class TestHipchatNotifier(unittest2.TestCase):
    def setUp(self):
        self.project_rooms = ['fakeroom1', 'fakeroom2']
        notifications_deploy = patch('tds.notifications.notifier.deploy', **{
            'find_hipchat_rooms_for_app.return_value': self.project_rooms[:]
        })

        notifications_deploy.start()

    def tearDown(self):
        patch.stopall()

    @patch('requests.api.request')
    def test_notify(self, request):
        h = tds.notifications.HipchatNotifier(
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
                    'from': deployment.actor['username'],
                    'message': (
                        '<strong>fake subj</strong><br />fake body'
                    ),
                },
                'headers': {'Content-Length': '0'}
            }


class TestGraphiteNotifier(unittest2.TestCase):
    def setUp(self):
        self.graphite_config = APP_CONFIG['notifications']['graphite']
        self.notifier = tds.notifications.GraphiteNotifier(
            APP_CONFIG,
            self.graphite_config
        )

        self.graphite = patch('graphiteudp.GraphiteUDPClient').start()

    def tearDown(self):
        patch.stopall()

    def test_inactive_event(self):
        with patch.object(self.notifier, 'active_events', ()):
            self.notifier.notify(DeploymentFactory())

        assert not self.graphite.called

    def test_active_event(self):
        d = DeploymentFactory()
        self.notifier.notify(d)

        self.graphite.assert_called_with(**dict(
            (x, self.graphite_config[x]) for x in ('host', 'port', 'prefix')
        ))

        self.graphite.return_value.send.assert_called_with(
            d.package['name'], 1
        )
