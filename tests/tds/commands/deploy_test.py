from mock import patch, Mock
from unittest_data_provider import data_provider
import unittest2
import logging

from tests.factories.model.deployment import DeploymentFactory
from tests.factories.utils.config import DeployConfigFactory
from tests.factories.model.project import ProjectFactory
from tests.factories.model.package import PackageFactory

import tagopsdb
import tagopsdb.deploy.deploy
import tds.commands
import tds.model
import tds.utils.config as tds_config


class DeploySetUp(unittest2.TestCase):
    def setUp(self):
        self.session = patch(
            'tagopsdb.Session',
            **{'commit.return_value': None}
        ).start()

        self.tds_package = patch(
            'tds.model.Package.get',
            **{'return_value': PackageFactory()}
        ).start()

        app_config = DeployConfigFactory()
        self.deploy = tds.commands.DeployController(app_config)
        self.config = tds.commands.ConfigController(app_config)

        deploy_methods = [
            ('get_app_info', (1, [1], {})),
            ('perform_deployments', None),
            ('find_app_deployments', {}),
            ('ensure_newer_versions', False),
            ('determine_new_deployments', ({}, {})),
            ('ensure_explicit_destinations', None),
            ('validate_project', lambda **kw:
                dict(project=ProjectFactory(name=kw['project']))
            )
        ]

        for (key, return_value) in deploy_methods:
            for obj in [self.deploy, self.config]:
                self.patch_method(obj, key, return_value)

    def tearDown(self):
        patch.stopall()

    def patch_method(self, obj, key, return_value):
        patcher = patch.object(obj, key)
        ptch = patcher.start()
        if callable(return_value):
            ptch.side_effect = return_value
        else:
            ptch.return_value = return_value


class TestPromoteAndPush(DeploySetUp):
    @data_provider(lambda: [(True,), (False,)])
    def test_check_previous_environment(self, force_option_used):
        self.deploy.requires_tier_progression = True
        self.patch_method(
            tagopsdb.deploy.deploy,
            'find_app_deployment',
            [(None,None,None,None)]
        )
        self.session = patch(
            'tagopsdb.Session',
            **{'commit.return_value': None}
        ).start()
        self.tds_authorize = patch(
            'tds.authorize',
            **{'verify_access.return_value': True}
        ).start()

        return_val = self.deploy.check_previous_environment(
            ProjectFactory(),
            params={'force': force_option_used,
                    'environment': 'prod',
                    'version': 'deadbeef'},
            pkg_id='123',
            app_id='123',
        )

        assert return_val == force_option_used

    def test_promote_new_version(self):
        self.patch_method(self.deploy, 'send_notifications', None)
        self.deploy.ensure_newer_versions.return_value = True

        self.deploy.action('promote',
            user_level='fake_access',
            environment='fake_env',
            project='fake_app'
        )

        assert self.deploy.perform_deployments.called

    @data_provider(lambda: [(True,), (False,)])
    def test_promote_version(self, version_is_new):
        self.patch_method(self.deploy, 'send_notifications', None)
        self.deploy.ensure_newer_versions.return_value = version_is_new

        self.deploy.action('promote',
            user_level='fake_access',
            environment='fake_env',
            project='fake_app'
        )

        assert self.deploy.perform_deployments.called

    def test_push_old_version(self):
        self.patch_method(self.config, 'send_notifications', None)
        self.config.ensure_newer_versions.return_value = False

        self.config.action('push',
            user_level='fake_access',
            environment='fake_env',
            project='fake_app'
        )

        assert self.config.perform_deployments.called

    @patch('tds.notifications.Notifications', autospec=True)
    def test_notifications_sent(self, Notifications):
        notify = Notifications.return_value.notify
        notify.return_value = None

        params = dict(
            user_level='fake_access',
            environment='test',  # TODO: mock BaseDeploy.envs
            project='fake_project',
            user='fake_user',
            groups=['engteam'],
            apptypes=['fake_apptype'],
            subcommand_name='promote',  # TODO: mock BaseDeploy.dep_types
            command_name='deploy',
            version='badf00d',
        )

        returned = self.deploy.action(params.get('subcommand_name'), **params)

        deployment = DeploymentFactory()
        Notifications.assert_called_with(DeployConfigFactory())

        notify.assert_called_with(deployment)


class TestAddApptype(DeploySetUp):
    @patch(
        'tagopsdb.deploy.repo.find_app_location',
        side_effect=tagopsdb.exceptions.RepoException)
    def test_missing_project(self, mock_app_loc):
        params = dict(
            user_level='fake_access',
            environment='test',  # TODO: mock BaseDeploy.envs
            project='fake_project',
            user='fake_user',
            groups=['engteam'],
            apptypes=['fake_apptype'],
            subcommand_name='add-apptype',  # TODO: mock BaseDeploy.dep_types
            command_name='deploy',
            version='badf00d',
        )

        res = self.deploy.action('add_apptype', **params)
        err = res.get('error', None)
        assert isinstance(err, Exception)
        assert params['project'] in err.args[1:], repr(err)

    @patch(
        'tagopsdb.deploy.repo.find_app_location',
        return_value=None)
    @patch(
        'tagopsdb.deploy.package.find_package_definition',
        return_value=None)
    @patch(
        'tagopsdb.deploy.repo.find_project',
        return_value=Mock(id='foo'))
    @patch(
        'tagopsdb.deploy.repo.add_app_packages_mapping',
        side_effect=tagopsdb.exceptions.RepoException)
    def test_missing_apptype(self, *args):
        params = dict(
            user_level='fake_access',
            environment='test',  # TODO: mock BaseDeploy.envs
            project='fake_project',
            user='fake_user',
            groups=['engteam'],
            apptype='fake_apptype',
            subcommand_name='add-apptype',  # TODO: mock BaseDeploy.dep_types
            command_name='deploy',
            version='badf00d',
        )

        res = self.deploy.action('add_apptype', **params)
        err = res.get('error', None)
        assert isinstance(err, Exception)
        assert 'fake_apptype' in err.args[1:]
