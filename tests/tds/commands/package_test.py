# Copyright 2016 Ifwe Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from mock import Mock, patch
from unittest_data_provider import data_provider
import unittest

from tests.factories.utils.config import DeployConfigFactory

import tds.commands
import tds.model

import tagopsdb


class TestPackageAdd(unittest.TestCase):
    def setUp(self):
        self.tds_project = patch(
            'tds.model.Project',
            **{'get.return_value': Mock(tds.model.Project)}
        )
        self.tds_project.start()

        self.tds_pkg_loc = patch(
            'tagopsdb.PackageLocation',
            **{'get.return_value': Mock(tagopsdb.PackageLocation)}
        )
        self.tds_pkg_loc.start()

        self.tds_pkg = patch(
            'tagopsdb.Package',
            **{'get.return_value': Mock(tagopsdb.Package)}
        )
        self.tds_pkg.start()

        self.package = tds.commands.PackageController(DeployConfigFactory())

        package_methods = [
            ('_queue_rpm', True),
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

        self.package.action('add', **dict(
            project='fake_app',
            version='deadbeef',
            user='fake_user',
            user_level='fake_access',
            repo={'incoming': 'fake_path'},
            force=force_option_used
        ))
