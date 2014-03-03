from mock import patch, Mock
import unittest2

from tests.fixtures.config import fake_config

import email
import tds.notifications
import tds.utils.config as tds_config

from tds.model import Deployment


class TestNotifications(unittest2.TestCase):

    def setUp(self):
        # fakeuser performs action:
        # tds deploy promote fake_project badf00d --apptypes=fake_apptype
        self.deployment = Deployment(
            actor=dict(
                username='fake_user',
                automated=False
            ),
            action=dict(
                command='deploy',
                subcommand='promote',
            ),
            project=dict(
                name='fake_project'
            ),
            package=dict(
                name='fake_project',  # TODO: make different from project name
                version='badf00d'
            ),
            target=dict(
                environment='test',
                apptypes=['fake_apptype'],
            )
        )

        self.project_rooms = ['fakeroom1', 'fakeroom2']

        self.app_config = tds_config.DottedDict(fake_config['deploy'])
        self.config = self.app_config['notifications']

        notifications_deploy = patch('tds.notifications.notifier.deploy', **{
            'find_hipchat_rooms_for_app.return_value': self.project_rooms[:]
        })

        notifications_deploy.start()

    def tearDown(self):
        patch.stopall()

    def create_notification(self):
        return tds.notifications.Notifications(self.app_config)

    def test_constructor(self):
        n = self.create_notification()

        assert n.config == self.config
        assert n.enabled_methods == self.config['enabled_methods']
        assert n.validation_time == self.config['validation_time']

    def test_send_notifications(self):
        n = self.create_notification()

        notifiers = {
            'email': Mock(spec=tds.notifications.EmailNotifier),
            'hipchat': Mock(spec=tds.notifications.HipchatNotifier)
        }

        with patch.object(n, '_notifiers', notifiers):

            subject, text = "fake_subj", "fake_body"
            n.notify(self.deployment)

            for mock in notifiers.values():
                assert mock.return_value.notify.called_with(self.deployment)

    @patch('smtplib.SMTP')
    def test_send_email(self, SMTP):
        n = self.create_notification()
        n.enabled_methods = ['email']
        n.notify(self.deployment)

        SMTP.assert_called_with('localhost')
        (sender, recvrs, content), _kw = SMTP.return_value.sendmail.call_args
        assert sender == self.deployment.actor['username']
        self.assertItemsEqual(
            recvrs,
            [self.deployment.actor['username']+'@tagged.com',
             self.config['email']['receiver']]
        )

        msg = email.message_from_string(content)
        sender_email = self.deployment.actor['username']+'@tagged.com'
        assert msg.get('content-type') == 'text/plain; charset="us-ascii"'
        assert msg.get('subject') == (
            '[TDS] Promote of version badf00d of fake_project on app tier(s)\n'
            ' fake_apptype in fakedev'
        )
        assert msg.get('from') == sender_email
        self.assertItemsEqual(
            msg.get('to').split(', '),
            [sender_email, self.config['email']['receiver']]
        )
        assert msg.get_payload() == (
            'fake_user performed a "tds deploy promote" for the following app '
            'tier(s) in fakedev:\n'
            '    fake_apptype'
        )

        assert SMTP.return_value.quit.called

    @patch('requests.api.request')
    def test_send_hipchat(self, request):
        n = self.create_notification()
        n.enabled_methods = ['hipchat']
        n.notify(self.deployment)

        rooms_callargs = zip(
            self.config['hipchat']['rooms'],
            request.call_args_list
        )

        for room, call_args in rooms_callargs:
            args, kwargs = call_args
            assert args == ('post', 'https://api.hipchat.com/v1/rooms/message')
            assert kwargs == {
                'data': None,
                'params': {
                    'auth_token': self.config['hipchat']['token'],
                    'room_id': room,
                    'from': self.deployment.actor['username'],
                    'message': (
                        '<strong>Promote of version badf00d of fake_project '
                        'on app tier(s) fake_apptype in fakedev</strong><br />'
                        'fake_user performed a "tds deploy promote" for the '
                        'following app tier(s) in fakedev:\n    fake_apptype'
                    ),
                },
                'headers': {'Content-Length': '0'}
            }


class TestNotifierClass(unittest2.TestCase):
    def test_send(self):
        n = tds.notifications.Notifier({}, {})
        self.assertRaises(
            NotImplementedError,
            n.notify,
            sender='string',
            project='string',
            apptypes=['list'],
            msg_subject='string',
            msg_text='string'
        )
