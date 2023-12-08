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

import contextlib
import mock
import unittest
import sys

from tests.factories.utils.config import (
    DeployConfigFactory,
    DatabaseTestConfigFactory
)

from py._io.capture import DontReadFromInput


# Monkey-patch pytest's io class--otherwise, salt tries to read the encoding
# and fails. This is fixed in much newer pytest than we can use:
# https://github.com/pytest-dev/pytest/commit/a3693ce50396e05910c9602443a825831d97a214
@property
def encoding(self):
    return sys.__stdin__.encoding


DontReadFromInput.encoding = encoding


import tds.apps.main  # noqa: E402


class TestTDS(unittest.TestCase):

    def setUp(self):
        config = DeployConfigFactory()

        mock.patch.object(
            tds.apps.main.TDS,
            '_load_config',
            return_value=config
        ).start()

        dbconfig = DatabaseTestConfigFactory()

        mock.patch.object(
            tds.apps.main.TDS,
            '_load_dbconfig',
            return_value=dbconfig
        ).start()

    def tearDown(self):
        mock.patch.stopall()

    def test_update_program_parameters(self):
        t = tds.apps.main.TDS(dict())

        with contextlib.nested(
            mock.patch(
                'pwd.getpwuid',
                **{'return_value.pw_name': 'fake'}
            ),
        ):
            t.update_program_parameters()

        self.assertEqual(t.params['user'], 'fake')
        self.assertEqual(t.params['env'], 'fakedev')

    def test_initialize_db_from_opts(self):

        init_session = mock.patch('tagopsdb.init', return_value=None)

        getpass = mock.patch('getpass.getpass', return_value='password')

        with contextlib.nested(getpass, init_session):
            t = tds.apps.main.TDS(dict(dbuser='user'))
            t.initialize_db()

            # init_session.assert_called_once_with('user', 'password')

    def test_initialize_db_from_config(self):
        init_session = mock.patch('tagopsdb.init', return_value=None)

        with contextlib.nested(init_session):
            t = tds.apps.main.TDS(dict(user_level='something'))
            t.initialize_db()

            # init_session.assert_called_once_with(
            #     'fakityfake', 'superpassword'
            # )

    @unittest.skip('empty test')
    def test_execute_command(self):
        pass
