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

    exclusive_options_fail_provider = lambda: [
        (dict(hosts=True, apptypes=True),),
        (dict(hosts=True, all_apptypes=True),),
        (dict(apptypes=True, all_apptypes=True),)
    ]

    @data_provider(exclusive_options_fail_provider)
    def test_check_exclusive_options_fail(self, params):
        t = tds.main.TDS(dict())
        t.params = dict(params)
        self.assertRaises(
            tds.main.ConfigurationError,
            t.check_exclusive_options
        )

    exclusive_options_success_provider = lambda: [
        (dict(hosts=True),),
        (dict(apptypes=True),),
        (dict(all_apptypes=True),),
        (dict(),),
    ]

    @data_provider(exclusive_options_success_provider)
    def test_check_exclusive_options_success(self, params):
        t = tds.main.TDS(dict())
        t.params = dict(params)
        t.check_exclusive_options()
        assert t.params['explicit'] == bool(len(params))

    def test_update_program_parameters(self):
        t = tds.main.TDS(dict())

        with contextlib.nested(
            mock.patch(
                'pwd.getpwuid',
                **{'return_value.pw_name': 'fake'}
            ),
            mock.patch.object(t, 'check_user_auth'),
        ):
            t.update_program_parameters()

        config = DeployConfigFactory()

        assert t.params['user'] == 'fake'
        assert t.params['environment'] == 'fakedev'
        assert t.params['repo'] == config['repo']

    def test_check_user_auth_failure(self):
        t = tds.main.TDS(dict(user='someone'))
        with mock.patch.object(t.authconfig, 'get_access_level', return_value=None):
            self.assertRaises(tds.main.AccessError, t.check_user_auth)

    def test_check_user_auth_succes(self):
        t = tds.main.TDS(dict(user='someone'))
        with mock.patch.object(t.authconfig, 'get_access_level', return_value='yay'):
            t.check_user_auth()
            assert t.params['user_level'] == 'yay'

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

            # init_session.assert_called_once_with('fakityfake', 'superpassword')

    @unittest2.skip('empty test')
    def test_execute_command(self):
        pass
