from mock import Mock, patch
from unittest_data_provider import data_provider
import unittest2
import logging

from tests.factories.utils.config import DeployConfigFactory

import tds.commands
import tds.model


class TestPackageAdd(unittest2.TestCase):
    def setUp(self):
        self.app_config = patch(
            'tds.utils.config.TDSDeployConfig',
            return_value=DeployConfigFactory(),
        )
        self.session = patch(
            'tagopsdb.database.meta.Session',
            **{'commit.return_value': None}
        ).start()
        self.tds_authorize = patch(
            'tds.authorize',
            **{'verify_access.return_value': True}
        ).start()

        self.package = tds.commands.Package(
            logging.getLogger(type(self).__name__ + ' Package')
        )

        package_methods = [
            ('_queue_rpm', True),
            ('check_package_state', 'Not_None'),
            ('wait_for_state_change', None),
        ]

        for (key, return_value) in package_methods:
            patcher = patch.object(self.package, key)
            ptch = patcher.start()
            ptch.return_value = return_value

    def tearDown(self):
        patch.stopall()

    add_provider = lambda: [
        (True,),
        (False,),
    ]

    @data_provider(add_provider)
    def test_add_package(self, force_option_used):
        self.package_module = patch(
            'tds.commands.package',
            **{'add_package.return_value': None,
               'find_package': Mock(status='completed')}
        ).start()
        self.repo_module = patch(
            'tagopsdb.deploy.repo',
            **{'find_app_location': Mock(pkg_name='fake_app', arch='noarch')}
        ).start()

        self.package.add(dict(
            project='fake_app',
            version='deadbeef',
            user='fake_user',
            user_level='fake_access',
            repo={'incoming': 'fake_path'},
            force=force_option_used
        ))