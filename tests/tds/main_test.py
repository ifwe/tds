import contextlib
import mock
import unittest2
from unittest_data_provider import data_provider

from tests.factories.utils.config import (
    DeployConfigFactory,
    DatabaseTestConfigFactory
)

import tds.main


class TestTDS(unittest2.TestCase):

    def setUp(self):
        config = DeployConfigFactory()

        mock.patch.object(
            tds.main.TDS,
            '_load_config',
            return_value=config
        ).start()

        dbconfig = DatabaseTestConfigFactory()

        mock.patch.object(
            tds.main.TDS,
            '_load_dbconfig',
            return_value=dbconfig
        ).start()

    def tearDown(self):
        mock.patch.stopall()

    def test_update_program_parameters(self):
        t = tds.main.TDS(dict())

        with contextlib.nested(
            mock.patch(
                'pwd.getpwuid',
                **{'return_value.pw_name': 'fake'}
            ),
        ):
            t.update_program_parameters()

        config = DeployConfigFactory()

        assert t.params['user'] == 'fake'
        assert t.params['env'] == 'fakedev'
        assert t.params['repo'] == config['repo']

    def test_initialize_db_from_opts(self):

        init_session = mock.patch('tagopsdb.init', return_value=None)

        getpass = mock.patch('getpass.getpass', return_value='password')

        with contextlib.nested(getpass, init_session):
            t = tds.main.TDS(dict(dbuser='user'))
            t.initialize_db()

            # init_session.assert_called_once_with('user', 'password')

    def test_initialize_db_from_config(self):
        init_session = mock.patch('tagopsdb.init', return_value=None)

        with contextlib.nested(init_session):
            t = tds.main.TDS(dict(user_level='something'))
            t.initialize_db()

            # init_session.assert_called_once_with(
            #     'fakityfake', 'superpassword'
            # )

    @unittest2.skip('empty test')
    def test_execute_command(self):
        pass
