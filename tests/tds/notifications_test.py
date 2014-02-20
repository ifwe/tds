from mock import patch
import contextlib
import unittest2

import email
import tds.notifications


class TestNotifications(unittest2.TestCase):

    def setUp(self):
        self.enabled_methods = ['hipchat', 'email']
        self.receiver_addr = 'someone@tagged.com'
        self.hipchat_rooms = ['fake1', 'fake2']
        self.hipchat_token = 'deadbeef'
        self.validation_time = 7200

        self.project_rooms = ['project_room1', 'project_room2']

        self.user = 'fake_user'
        self.project = 'fake_project'
        self.apptypes = ['fake_apptype']

        tds_utils = patch('tds.utils', **{
            'verify_conf_file_section.return_value': (
                self.enabled_methods[:], self.receiver_addr,
                self.hipchat_rooms[:], self.hipchat_token,
                self.validation_time
            )
        })

        notifications_deploy = patch('tds.notifications.deploy', **{
            'find_hipchat_rooms_for_app.return_value': self.project_rooms[:]
        })

        for ptch in [tds_utils, notifications_deploy]:
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
        assert n.sender_addr == (self.user + '@tagged.com')
        assert n.enabled_methods == self.enabled_methods
        assert n.receiver_addr == self.receiver_addr
        assert n.hipchat_rooms == self.hipchat_rooms + self.project_rooms
        assert n.hipchat_token == self.hipchat_token
        assert n.validation_time == self.validation_time

    def test_send_notifications(self):
        n = self.create_notification()

        patched_methods = ['send_' + mth for mth in self.enabled_methods[:]]
        subject, text = "fake_subj", "fake_body"

        with contextlib.nested(
            *[patch.object(n, mth) for mth in patched_methods]
        ):
            n.send_notifications(subject, text)

            for mth in patched_methods:
                assert getattr(n, mth).called_with(subject, text)

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
            [self.user+'@tagged.com', self.receiver_addr]
        )

        msg = email.message_from_string(content)
        assert msg.get('content-type') == 'text/plain; charset="us-ascii"'
        assert msg.get('subject') == ('[TDS] fake_subj')
        assert msg.get('from') == (self.user+'@tagged.com')
        self.assertItemsEqual(
            msg.get('to').split(', '),
            [self.user+'@tagged.com', self.receiver_addr]
        )
        assert msg.get_payload() == 'fake_body'

        assert SMTP.return_value.quit.called
