from mock import patch
import unittest2
import logging

import tds.commands

#class TestPromote(unittest2.TestCase):
class TestPromote(unittest2.TestCase):
    def setUp(self):

        self.deploy = tds.commands.Deploy(logging.getLogger(type(self).__name__))

        deploy_methods = [
            'get_app_info',
            'send_notifications',
            'verify_project_type',
            'perform_deployments',
            'find_app_deployments',
            'ensure_newer_versions',
            'determine_new_deployments',
            'ensure_explicit_destinations',
        ]

        for key in deploy_methods:
            ptch = patch.object(self.deploy, key)
            setattr(self, key, ptch.start())

        self.get_app_info.return_value = (None, None, None)
        self.send_notifications.return_value = None
        self.perform_deployments.return_value = None
        self.verify_project_type.return_value = 'fake_app'
        self.find_app_deployments.return_value = {}
        self.determine_new_deployments.return_value = None, None
        self.ensure_explicit_destinations.return_value = None

        self.session = patch('tds.commands.Session', **{'commit.return_value': None}).start()
        self.tds_authorize = patch('tds.authorize', **{'verify_access.return_value': True}).start()

    def tearDown(self):
        patch.stopall()

    def test_promote_new_version(self):
        self.ensure_newer_versions.return_value = True

        self.deploy.promote(dict(
            user_level = 'fake_access',
            environment = 'fake_env',
            project = 'fake_app'
        ))

        assert self.deploy.perform_deployments.called

    def test_promote_old_version(self):
        self.ensure_newer_versions.return_value = False

        self.deploy.promote(dict(
            user_level = 'fake_access',
            environment = 'fake_env',
            project = 'fake_app'
        ))

        assert not self.deploy.perform_deployments.called


if __name__ == '__main__':
    pass
