import contextlib
import mock
import unittest2
import yaml
from unittest_data_provider import data_provider

from tests.fixtures.config import fake_config

import tds.main


class TestTDS(unittest2.TestCase):
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
        m = mock.mock_open(read_data=yaml.dump(fake_config['deploy']))

        with contextlib.nested(
            mock.patch(
                'pwd.getpwuid',
                **{'return_value.pw_name': 'fake'}
            ),
            mock.patch.object(t, 'check_user_auth'),
            mock.patch('__builtin__.open', m, create=True),
        ):
            t.update_program_parameters()

        assert t.params['user'] == 'fake'
        assert t.params['environment'] == 'fakedev'
        assert t.params['repo'] == fake_config['deploy']['repo']

    def test_check_user_auth_failure(self):
        t = tds.main.TDS(dict(user='someone'))
        with mock.patch('tds.authorize.get_access_level', return_value=None):
            self.assertRaises(tds.main.AccessError, t.check_user_auth)

    def test_check_user_auth_succes(self):
        t = tds.main.TDS(dict(user='someone'))
        with mock.patch('tds.authorize.get_access_level', return_value='yay'):
            t.check_user_auth()
            assert t.params['user_level'] == 'yay'

    def test_initialize_db_from_opts(self):
        t = tds.main.TDS(dict(dbuser='user'))

        init_session = mock.patch.object(
            tds.main,
            'init_session',
            return_value=None
        )

        getpass = mock.patch('getpass.getpass', return_value='password')

        with contextlib.nested(getpass, init_session):
            t.initialize_db()
            tds.main.init_session.assert_called_once_with('user', 'password')

    def test_initialize_db_from_config(self):
        t = tds.main.TDS(dict(user_level='something'))

        init_session = mock.patch.object(
            tds.main,
            'init_session',
            return_value=None
        )

        m = mock.mock_open(read_data=yaml.dump(fake_config['database']))
        with contextlib.nested(
            mock.patch('__builtin__.open', m, create=True),
            init_session
        ):
            t.initialize_db()
            tds.main.init_session.assert_called_once_with(
                'fakityfake',
                'superpassword'
            )

    def test_execute_command(self):
        pass
