from mock import patch
import unittest2
import logging

import tds.commands

#class TestPromote(unittest2.TestCase):
class TestPromoteAndPush(unittest2.TestCase):
    def setUp(self):

        self.deploy = tds.commands.Deploy(logging.getLogger(type(self).__name__ + ' Deploy'))
        self.config = tds.commands.Config(logging.getLogger(type(self).__name__ + 'Config'))

        deploy_methods = [
            ('get_app_info', (None, None, None)),
            ('send_notifications', None),
            ('perform_deployments', None),
            ('verify_project_type', 'fake_app'),
            ('find_app_deployments', {}),
            ('ensure_newer_versions', False),
            ('determine_new_deployments', (None, None)),
            ('ensure_explicit_destinations', None),
        ]

        for (key, return_value) in deploy_methods:
            for obj in [self.deploy, self.config]:
                patcher = patch.object(obj, key)
                ptch = patcher.start()
                ptch.return_value = return_value

        self.session = patch('tds.commands.Session', **{'commit.return_value': None}).start()
        self.tds_authorize = patch('tds.authorize', **{'verify_access.return_value': True}).start()

    def tearDown(self):
        patch.stopall()

    def test_promote_new_version(self):
        self.deploy.ensure_newer_versions.return_value = True

        self.deploy.promote(dict(
            user_level = 'fake_access',
            environment = 'fake_env',
            project = 'fake_app'
        ))

        assert self.deploy.perform_deployments.called

    def test_promote_old_version(self):
        self.deploy.ensure_newer_versions.return_value = False

        self.deploy.promote(dict(
            user_level = 'fake_access',
            environment = 'fake_env',
            project = 'fake_app'
        ))

        assert not self.deploy.perform_deployments.called

    def test_push_new_version(self):
        self.config.ensure_newer_versions.return_value = True

        self.config.push(dict(
            user_level = 'fake_access',
            environment = 'fake_env',
            project = 'fake_app'
        ))

        assert self.config.perform_deployments.called

    def test_push_old_version(self):
        self.config.ensure_newer_versions.return_value = False

        self.config.push(dict(
            user_level = 'fake_access',
            environment = 'fake_env',
            project = 'fake_app'
        ))

        assert not self.config.perform_deployments.called



if __name__ == '__main__':
    pass
