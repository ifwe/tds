from mock import Mock, patch
from unittest_data_provider import data_provider
import unittest2
import logging

from tests.factories.utils.config import DeployConfigFactory

import tagopsdb.deploy.deploy
import tds.commands
import tds.model
import tds.utils.config as tds_config


class _Base(unittest2.TestCase):
    def setUp(self):
        self.app_config = patch(
            'tds.utils.config.TDSDeployConfig',
            return_value=DeployConfigFactory(),
        )
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

    force_provider = staticmethod(lambda: [
        (True,),
        (False,),
    ])


class TestPackageAdd(_Base):
    def setUp(self):
        super(TestPackageAdd, self).setUp()

        self.package = tds.commands.Package(
            logging.getLogger(type(self).__name__ + ' Package')
        )

        package_methods = [
            ('_queue_rpm', True),
        ]

        for (key, return_value) in package_methods:
            for obj in [self.package]:
                self.patch_method(obj, key, return_value)

    add_provider = lambda: [
        (True, 'Not_None'),
        (False, 'Not_None'),
    ]

    @data_provider(add_provider)
    def test_add_package(self, force_option_used, pkg_state):
        self.package_module = patch(
            'tds.commands.package',
            **{'add_package.return_value': None}
        )
        self.repo_module = patch(
            'tds.commands.repo',
            **{'find_app_location': Mock(pkg_name='fake_app', arch='noarch')}
        )
        self.patch_method(self.package, 'check_package_state', pkg_state)
        self.patch_method(self.package, 'wait_for_state_change', None)

        self.package.add(dict(
            project='fake_app',
            version='deadbeef',
            user='fake_user',
            user_level='fake_access',
            repo={'incoming': 'fake_path'}
        ))

class TestPromoteAndPush(_Base):
    def setUp(self):
        super(TestPromoteAndPush, self).setUp()

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

    @data_provider(_Base.force_provider)
    def test_check_previous_environment(self, force_option_used):
        self.deploy.requires_tier_progression = True
        self.patch_method(
            tagopsdb.deploy.deploy,
            'find_app_deployment',
            None
        )

        return_val = self.deploy.check_previous_environment(
            params={'force': force_option_used,
                    'environment': 'prod',
                    'project': 'fake_app',
                    'version': 'deadbeef'},
            pkg_id='123',
            app_id='123',
        )

        assert return_val == force_option_used

    def test_promote_new_version(self):
        self.patch_method(self.deploy, 'send_notifications', None)
        self.deploy.ensure_newer_versions.return_value = True

        self.deploy.promote(dict(
            user_level='fake_access',
            environment='fake_env',
            project='fake_app'
        ))

        assert self.deploy.perform_deployments.called

    promote_versions_provider = lambda: [
        (True,),
        (False,)
    ]

    @data_provider(promote_versions_provider)
    def test_promote_version(self, version_is_new):
        self.patch_method(self.deploy, 'send_notifications', None)
        self.deploy.ensure_newer_versions.return_value = version_is_new

        self.deploy.promote(dict(
            user_level='fake_access',
            environment='fake_env',
            project='fake_app'
        ))

        assert self.deploy.perform_deployments.called

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

        params = dict(
            user_level='fake_access',
            environment='test',  # TODO: mock BaseDeploy.envs
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
                environment='test',
                apptypes=['whatever'],
            )
        )

        Notifications.assert_called_with(tds_config.TDSDeployConfig())

        notify.assert_called_with(deployment)
