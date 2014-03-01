from mock import patch, Mock
import unittest2
import logging

from tests.fixtures.config import fake_config

import tds.commands
import tds.model
import tds.utils.config as tds_config


class TestPromoteAndPush(unittest2.TestCase):
    def setUp(self):

        self.app_config = patch(
            'tds.utils.config.TDSDeployConfig',
            **{
                'return_value': tds_config.DottedDict(fake_config['deploy']),
                'return_value.load': Mock(return_value=None),
            }
        )

        self.deploy = tds.commands.Deploy(
            logging.getLogger(type(self).__name__ + ' Deploy')
        )
        self.config = tds.commands.Config(
            logging.getLogger(type(self).__name__ + ' Config')
        )

        deploy_methods = [
            ('get_app_info', (None, None, None)),
            ('perform_deployments', None),
            ('verify_project_type', 'fake_app'),
            ('find_app_deployments', {}),
            ('ensure_newer_versions', False),
            ('determine_new_deployments', (None, None)),
            ('ensure_explicit_destinations', None),
        ]

        for (key, return_value) in deploy_methods:
            for obj in [self.deploy, self.config]:
                self.patch_method(obj, key, return_value)

        self.session = patch(
            'tds.commands.Session',
            **{'commit.return_value': None}
        ).start()
        self.tds_authorize = patch(
            'tds.authorize',
            **{'verify_access.return_value': True}
        ).start()

    def tearDown(self):
        patch.stopall()

    def patch_method(self, obj, key, return_value):
        patcher = patch.object(obj, key)
        ptch = patcher.start()
        ptch.return_value = return_value

    def test_promote_new_version(self):
        self.patch_method(self.deploy, 'send_notifications', None)
        self.deploy.ensure_newer_versions.return_value = True

        self.deploy.promote(dict(
            user_level='fake_access',
            environment='fake_env',
            project='fake_app'
        ))

        assert self.deploy.perform_deployments.called

    def test_promote_old_version(self):
        self.patch_method(self.deploy, 'send_notifications', None)
        self.deploy.ensure_newer_versions.return_value = False

        self.deploy.promote(dict(
            user_level='fake_access',
            environment='fake_env',
            project='fake_app'
        ))

        assert self.deploy.perform_deployments.called

    def test_push_new_version(self):
        self.patch_method(self.config, 'send_notifications', None)
        self.config.ensure_newer_versions.return_value = True

        self.config.push(dict(
            user_level='fake_access',
            environment='fake_env',
            project='fake_app'
        ))

        assert self.config.perform_deployments.called

    def test_push_old_version(self):
        self.patch_method(self.config, 'send_notifications', None)
        self.config.ensure_newer_versions.return_value = False

        self.config.push(dict(
            user_level='fake_access',
            environment='fake_env',
            project='fake_app'
        ))

        assert self.config.perform_deployments.called

    @patch('tds.notifications.Notifications', autospec=True)
    def test_notifications_sent(self, Notifications):
        notify = Notifications.return_value.notify
        notify.return_value = None

        # msg_subject = (
        #     'Deployment of version unknown of fake_app on app '
        #     'tier(s) whatever in development'
        # )
        # msg_text = (
        #     'fake_user performed a "tds package promote" for the following'
        #     ' app tier(s) in development:\n    whatever'
        # )

        params = dict(
            user_level='fake_access',
            environment='dev',  # TODO: mock BaseDeploy.envs
            project='fake_app',
            user='fake_user',
            apptypes=['whatever'],
            subcommand_name='promote',  # TODO: mock BaseDeploy.dep_types
            command_name='package',
            version='deadbeef',
        )

        getattr(self.deploy, params.get('subcommand_name'))(params)

        deployment = tds.model.Deployment(
            actor=dict(
                username='fake_user',
                automated=False
            ),
            action=dict(
                command='package',
                subcommand='promote',
            ),
            project=dict(
                name='fake_app'
            ),
            package=dict(
                name='fake_app',  # TODO: make different from project name
                version='deadbeef'
            ),
            target=dict(
                apptypes=['whatever']
            )
        )

        Notifications.assert_called_with(tds_config.TDSDeployConfig())

        notify.assert_called_with(deployment)
