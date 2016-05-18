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

import mock
import unittest
from unittest_data_provider import data_provider

import yaml
import os.path
import tds.utils.config as config

import tests
import tests.factories.utils.config as config_factories


class TestDottedDict(unittest.TestCase):
    def setUp(self):
        self.d = config.DottedDict(a=dict(b=dict(c=1)))

    def test_getitem_hit(self):
        self.assertEqual(self.d['a.b.c'], 1)

    def test_getitem_miss(self):
        self.assertRaises(KeyError, self.d.__getitem__, 'a.b.d')

    def test_getitem_miss_default(self):
        self.assertEqual(self.d.__getitem__(key='a.b.d', default='foo'), 'foo')


class TestConfig(unittest.TestCase):
    def test_load(self):
        c = config.Config()
        self.assertRaises(NotImplementedError, c.load)


class FileConfigLoader(object):
    def load_fake_config(self, c, fixture_id):
        fname = os.path.join(
            tests.FIXTURES_PATH,
            'config',
            fixture_id + '.yml'
        )

        m = mock.mock_open(read_data=open(fname).read())
        with mock.patch('__builtin__.open', m, create=True):
            c.load()

        m.assert_called_with(c.filename)


class TestFileConfig(unittest.TestCase, FileConfigLoader):
    def test_constructor(self):
        c = config.FileConfig('foo')
        self.assertEqual(c.filename, 'foo')

    def test_load_success(self):
        c = config.FileConfig('foo')

        with mock.patch.object(c, 'parse') as mock_parse:
            mock_parse.return_value = {}
            self.load_fake_config(c, 'deploy')

    def test_load_read_failure(self):
        c = config.FileConfig('foo')

        m = mock.mock_open()
        with mock.patch('__builtin__.open', m, create=True):
            m.return_value.read.side_effect = IOError
            self.assertRaises(config.ConfigurationError, c.load)

    def test_load_open_failure(self):
        c = config.FileConfig('foo')

        m = mock.mock_open()
        with mock.patch('__builtin__.open', m, create=True):
            m.side_effect = IOError
            self.assertRaises(config.ConfigurationError, c.load)

    def test_parse_notimplemented(self):
        c = config.FileConfig('foo')
        self.assertRaises(NotImplementedError, c.parse, data=None)


class TestYAMLConfig(unittest.TestCase):
    def setUp(self):
        self.fake_config = dict(
            string='a string',
            number=1234,
            nested=dict(
                float=3.14159
            ),
            list=['a', 1, None]
        )

    def test_parse_success(self):
        c = config.YAMLConfig('foo')
        self.assertEqual(
            self.fake_config, c.parse(yaml.dump(self.fake_config))
        )

    def test_parse_invalid_yaml(self):
        c = config.YAMLConfig('foo')
        config_data = yaml.dump(self.fake_config)
        config_data += 'this is some invalid yaml\nE%&*O(O*&^%E$'
        self.assertRaises(config.ConfigurationError, c.parse, data=config_data)

    def test_parse_non_dict_yaml(self):
        c = config.YAMLConfig('foo')
        config_data = yaml.dump([self.fake_config])
        self.assertRaises(config.ConfigurationError, c.parse, data=config_data)


class TestVerifyingConfig(unittest.TestCase):

    def test_super_load(self):
        class LoadImplemented(config.Config):
            def load(self):
                pass

        class VerifyingConfigSubclass(config.VerifyingConfig, LoadImplemented):
            pass

        c = VerifyingConfigSubclass()
        with mock.patch.object(c, 'verify'):
            c.load()
            c.verify.assert_called()

    def test_verify_empty(self):
        with mock.patch.object(config.VerifyingConfig, '_verify'):
            c = config.VerifyingConfig()
            with mock.patch.object(c, 'load'):
                c.load.return_value = None
                c.verify()

                c.load.assert_called_with()

            config.VerifyingConfig._verify.assert_called_with(
                c, c.schema
            )

    def test_verify_non_empty(self):
        with mock.patch.object(config.VerifyingConfig, '_verify'):
            c = config.VerifyingConfig()
            with mock.patch.object(c, 'load'):
                c['something'] = 'foo'
                c.load.return_value = None
                c.verify()

                self.assertFalse(c.load.called)

            config.VerifyingConfig._verify.assert_called_with(
                c, c.schema
            )

    def test__verify_success_empty_schema(self):
        config.VerifyingConfig._verify(data={}, schema={})

    def test__verify_success_contents(self):
        config.VerifyingConfig._verify(
            data=dict(a=dict(b=1, c=2)),
            schema=dict(a=['b', 'c']),
        )

    def test__verify_failure_missing_toplevel_key(self):
        self.assertRaises(
            config.ConfigurationError,
            config.VerifyingConfig._verify,
            data=dict(a=dict(b=1, c=2)),
            schema=dict(a=['b', 'c'], d=['e']),
        )

    def test__verify_failure_missing_sub_key(self):
        self.assertRaises(
            config.ConfigurationError,
            config.VerifyingConfig._verify,
            data=dict(a=dict(b=1, c=2), d=dict()),
            schema=dict(a=['b', 'c'], d=['e']),
        )

    def test__verify_failure_weird_type(self):
        self.assertRaises(
            config.ConfigurationError,
            config.VerifyingConfig._verify,
            data=dict(a=dict(b=1, c=2), d=1),
            schema=dict(a=['b', 'c'], d=['e']),
        )

    def test__verify_failure_extra_sub_key(self):
        self.assertRaises(
            config.ConfigurationError,
            config.VerifyingConfig._verify,
            data=dict(a=dict(b=1, c=2), d=dict(e=3, f=4)),
            schema=dict(a=['b', 'c'], d=['e']),
        )


class TestTDSConfig(unittest.TestCase):
    def test_constructor_with_default(self):
        c = config.TDSConfig('foo')
        self.assertEqual(c.filename, '%s/%s' % (c.default_conf_dir, 'foo'))

    def test_constructor_without_default(self):
        c = config.TDSConfig('foo', '/fake/dir')
        self.assertEqual(c.filename, '/fake/dir/foo')


class TestTDSDatabaseConfig(unittest.TestCase, FileConfigLoader):
    constructor_kwargs_expected = lambda: [
        (
            dict(access_level='foo', base_name_fragment='bar'),
            '%s/%s.foo.yml' % (
                config.TDSDatabaseConfig.default_conf_dir,
                config.TDSDatabaseConfig.default_name_fragment
            )
        ),
        (
            dict(
                access_level='foo',
                name_fragment='whatever',
                base_name_fragment='bar',
            ),
            ('%s/%s.foo.yml' %
                (config.TDSDatabaseConfig.default_conf_dir, 'whatever'))
        ),
        (
            dict(
                access_level='foo',
                conf_dir='/fake/dir',
                base_name_fragment='bar',
            ),
            ('/fake/dir/%s.foo.yml' %
                config.TDSDatabaseConfig.default_name_fragment)
        ),
        (
            dict(
                access_level='foo',
                conf_dir='/fake/dir',
                name_fragment='whatever',
                base_name_fragment='bar',
            ),
            '/fake/dir/whatever.foo.yml'
        ),

    ]

    @data_provider(constructor_kwargs_expected)
    def test_constructor(self, kwargs, expected):
        c = config.TDSDatabaseConfig(**kwargs)
        self.assertEqual(c.filename, expected)

    def test_schema_success(self):
        c = config.TDSDatabaseConfig('foo', 'bar')
        self.load_fake_config(c, 'dbaccess.test')

        fake_config = config_factories.DatabaseTestConfigFactory()

        self.assertEqual(c['db.user'], fake_config['db']['user'])
        self.assertEqual(c['db.password'], fake_config['db']['password'])

    def test_schema_failure(self):
        c = config.TDSDatabaseConfig('foo', 'bar')
        self.load_fake_config(c, 'dbaccess.test')
        c['db'].pop('user')
        self.assertRaises(config.ConfigurationError, c.verify)


class TestTDSDeployConfig(unittest.TestCase, FileConfigLoader):
    constructor_kwargs_expected = lambda: [
        (
            {},
            '%s/%s.yml' % (
                config.TDSDeployConfig.default_conf_dir,
                config.TDSDeployConfig.default_name_fragment
            )
        ),
        (
            dict(name_fragment='whatever'),
            '%s/whatever.yml' % config.TDSDeployConfig.default_conf_dir
        ),
        (
            dict(conf_dir='/fake/dir'),
            ('/fake/dir/%s.yml' %
                config.TDSDeployConfig.default_name_fragment)
        ),
        (
            dict(
                conf_dir='/fake/dir',
                name_fragment='whatever'
            ),
            '/fake/dir/whatever.yml'
        ),

    ]

    @data_provider(constructor_kwargs_expected)
    def test_constructor(self, kwargs, expected):
        c = config.TDSDeployConfig(**kwargs)
        self.assertEqual(c.filename, expected)

    def test_schema_success(self):
        c = config.TDSDeployConfig('foo')
        self.load_fake_config(c, 'deploy')
        fake_config = config_factories.DeployConfigFactory()
        self.assertEqual(c, fake_config)

    def test_dotted_key_hit(self):
        c = config.TDSDeployConfig('foo')
        self.load_fake_config(c, 'deploy')
        self.assertEqual(c['notifications.hipchat.token'], 'deadbeef')

    def test_dotted_key_miss(self):
        c = config.TDSDeployConfig('foo')
        self.load_fake_config(c, 'deploy')
        self.assertRaises(KeyError, lambda: c['notifications.hipchat.missing'])

    def test_dotted_key_miss_default(self):
        c = config.TDSDeployConfig('foo')
        self.load_fake_config(c, 'deploy')
        self.assertEqual(
            'default', c.get('notifications.hipchat.missing', 'default')
        )
