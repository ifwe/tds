from mock import patch
import contextlib
import unittest2

import tds.notifications


class TestNotifications(unittest2.TestCase):

    def setUp(self):
        self.enabled_methods = ['hipchat']
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
        )})

        notifications_deploy = patch('tds.notifications.deploy', **{
            'find_hipchat_rooms_for_app.return_value': self.project_rooms[:]
        })

        for ptch in [tds_utils, notifications_deploy]:
            ptch.start()

    def tearDown(self):
        patch.stopall()

    def test_constructor(self):

        n = tds.notifications.Notifications(self.project, self.user, self.apptypes)

        assert n.sender == self.user
        assert n.sender_addr == (self.user + '@tagged.com')
        assert n.enabled_methods == self.enabled_methods
        assert n.receiver_addr == self.receiver_addr
        assert n.hipchat_rooms == self.hipchat_rooms + self.project_rooms
        assert n.hipchat_token == self.hipchat_token
        assert n.validation_time == self.validation_time

