from mock import patch, Mock
import unittest2

from tests.fixtures.config import fake_config

import email
import tds.notifications
import tds.utils.config as tds_config


class TestNotifications(unittest2.TestCase):

    def setUp(self):

        self.not_cfg = fake_config['deploy']['notifications']

        self.project_rooms = ['project_room1', 'project_room2']

        self.user = 'fake_user'
        self.project = 'fake_project'
        self.apptypes = ['fake_apptype']

        notifications_deploy = patch('tds.notifications.notifier.deploy', **{
            'find_hipchat_rooms_for_app.return_value': self.project_rooms[:]
        })

        config = patch(
            'tds.utils.config.TDSDeployConfig',
            **{
                'return_value': tds_config.DottedDict(fake_config['deploy']),
                'return_value.load': Mock(return_value=None),
            }
        )

        for ptch in [notifications_deploy, config]:
            ptch.start()

    def tearDown(self):
        patch.stopall()

    def create_notification(self):
        return tds.notifications.Notifications(
            self.project,
            self.user,
            self.apptypes
        )

    def test_constructor(self):
        n = self.create_notification()

        assert n.sender == self.user
        assert n.enabled_methods == self.not_cfg['enabled_methods']
        assert n.validation_time == self.not_cfg['validation_time']

    def test_send_notifications(self):
        n = self.create_notification()

        notifiers = {
            'email': Mock(spec=tds.notifications.EmailNotifier),
            'hipchat': Mock(spec=tds.notifications.HipchatNotifier)
        }

        with patch.object(n, '_notifiers', notifiers):

            subject, text = "fake_subj", "fake_body"
            n.send_notifications(subject, text)

            for mock in notifiers.values():
                assert mock.return_value.send.called_with(
                    n.sender,
                    n.project,
                    n.apptypes,
                    subject,
                    text
                )

    @patch('smtplib.SMTP')
    def test_send_email(self, SMTP):
        n = self.create_notification()
        n.enabled_methods = ['email']
        n.send_notifications('fake_subj', 'fake_body')

        SMTP.assert_called_with('localhost')
        (sender, recvrs, content), _kw = SMTP.return_value.sendmail.call_args
        assert sender == self.user
        self.assertItemsEqual(
            recvrs,
            [self.user+'@tagged.com', self.not_cfg['email']['receiver']]
        )

        msg = email.message_from_string(content)
        assert msg.get('content-type') == 'text/plain; charset="us-ascii"'
        assert msg.get('subject') == ('[TDS] fake_subj')
        assert msg.get('from') == (self.user+'@tagged.com')
        self.assertItemsEqual(
            msg.get('to').split(', '),
            [self.user+'@tagged.com', self.not_cfg['email']['receiver']]
        )
        assert msg.get_payload() == 'fake_body'

        assert SMTP.return_value.quit.called

    @patch('requests.api.request')
    def test_send_hipchat(self, request):
        n = self.create_notification()
        n.enabled_methods = ['hipchat']
        n.send_notifications('fake_subj', 'fake_body')

        rooms_callargs = zip(
            self.not_cfg['hipchat']['rooms'],
            request.call_args_list
        )

        for room, call_args in rooms_callargs:
            args, kwargs = call_args
            assert args == ('post', 'https://api.hipchat.com/v1/rooms/message')
            assert kwargs == {
                'data': None,
                'params': {
                    'auth_token': self.not_cfg['hipchat']['token'],
                    'room_id': room,
                    'from': self.user,
                    'message': ('<strong>fake_subj</strong><br />fake_body'),
                },
                'headers': {'Content-Length': '0'}
            }
