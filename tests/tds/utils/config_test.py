import mock
import unittest2
from unittest_data_provider import data_provider

import yaml
import os.path
import tds.utils.config as config

import tests
import tests.factories


class TestDottedDict(unittest2.TestCase):
    def setUp(self):
        self.d = config.DottedDict(a=dict(b=dict(c=1)))

    def test_getitem_hit(self):
        assert self.d['a.b.c'] == 1

    def test_getitem_miss(self):
        self.assertRaises(KeyError, self.d.__getitem__, 'a.b.d')

    def test_getitem_miss_default(self):
        assert self.d.__getitem__(key='a.b.d', default='foo') == 'foo'


class TestConfig(unittest2.TestCase):
    def test_load(self):
        c = config.Config()
        self.assertRaises(NotImplementedError, c.load, logger=None)


class FileConfigLoader(object):
    def load_fake_config(self, c, fixture_id):
        fname = os.path.join(
            tests.FIXTURES_PATH,
            'config',
            fixture_id + '.yml'
        )

        m = mock.mock_open(read_data=open(fname).read())
        with mock.patch('__builtin__.open', m, create=True):
            c.load(logger=None)

        m.assert_called_once_with(c.filename)


class TestFileConfig(unittest2.TestCase, FileConfigLoader):
    def test_constructor(self):
        c = config.FileConfig('foo')
        assert c.filename == 'foo'

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
            self.assertRaises(config.ConfigurationError, c.load, logger=None)

    def test_load_open_failure(self):
        c = config.FileConfig('foo')

        m = mock.mock_open()
        with mock.patch('__builtin__.open', m, create=True):
            m.side_effect = IOError
            self.assertRaises(config.ConfigurationError, c.load, None)

    def test_parse_notimplemented(self):
        c = config.FileConfig('foo')
        self.assertRaises(NotImplementedError, c.parse, data=None)


class TestYAMLConfig(unittest2.TestCase):
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
        assert self.fake_config == c.parse(yaml.dump(self.fake_config))

    def test_parse_invalid_yaml(self):
        c = config.YAMLConfig('foo')
        config_data = yaml.dump(self.fake_config)
        config_data += 'this is some invalid yaml\nE%&*O(O*&^%E$'
        self.assertRaises(config.ConfigurationError, c.parse, data=config_data)

    def test_parse_non_dict_yaml(self):
        c = config.YAMLConfig('foo')
        config_data = yaml.dump([self.fake_config])
        self.assertRaises(config.ConfigurationError, c.parse, data=config_data)


class TestVerifyingConfig(unittest2.TestCase):

    def test_super_load(self):
        class LoadImplemented(config.Config):
            def load(self, logger=None):
                pass

        class VerifyingConfigSubclass(config.VerifyingConfig, LoadImplemented):
            pass

        c = VerifyingConfigSubclass()
        with mock.patch.object(c, 'verify'):
            c.load(logger=None)
            c.verify.assert_called()

    def test_verify_empty(self):
        with mock.patch.object(config.VerifyingConfig, '_verify'):
            c = config.VerifyingConfig()
            with mock.patch.object(c, 'load'):
                c.load.return_value = None
                c.verify(logger=None)

                c.load.assert_called_with(None)

            config.VerifyingConfig._verify.assert_called_with(
                c, c.schema, None
            )

    def test_verify_non_empty(self):
        with mock.patch.object(config.VerifyingConfig, '_verify'):
            c = config.VerifyingConfig()
            with mock.patch.object(c, 'load'):
                c['something'] = 'foo'
                c.load.return_value = None
                c.verify(logger=None)

                assert not c.load.called

            config.VerifyingConfig._verify.assert_called_with(
                c, c.schema, None
            )

    def test__verify_success_empty_schema(self):
        config.VerifyingConfig._verify(data={}, schema={}, logger=None)

    def test__verify_success_contents(self):
        config.VerifyingConfig._verify(
            data=dict(a=dict(b=1, c=2)),
            schema=dict(a=['b', 'c']),
            logger=None
        )
        assert True, "Everything's ok if we get here!"

    def test__verify_failure_missing_toplevel_key(self):
        self.assertRaises(
            config.ConfigurationError,
            config.VerifyingConfig._verify,
            data=dict(a=dict(b=1, c=2)),
            schema=dict(a=['b', 'c'], d=['e']),
            logger=None
        )

    def test__verify_failure_missing_sub_key(self):
        self.assertRaises(
            config.ConfigurationError,
            config.VerifyingConfig._verify,
            data=dict(a=dict(b=1, c=2), d=dict()),
            schema=dict(a=['b', 'c'], d=['e']),
            logger=None
        )

    def test__verify_failure_weird_type(self):
        self.assertRaises(
            config.ConfigurationError,
            config.VerifyingConfig._verify,
            data=dict(a=dict(b=1, c=2), d=1),
            schema=dict(a=['b', 'c'], d=['e']),
            logger=None
        )

    def test__verify_failure_extra_sub_key(self):
        self.assertRaises(
            config.ConfigurationError,
            config.VerifyingConfig._verify,
            data=dict(a=dict(b=1, c=2), d=dict(e=3, f=4)),
            schema=dict(a=['b', 'c'], d=['e']),
            logger=None
        )


class TestTDSConfig(unittest2.TestCase):
    def test_constructor_with_default(self):
        c = config.TDSConfig('foo')
        assert c.filename == '%s/%s' % (c.default_conf_dir, 'foo')

    def test_constructor_without_default(self):
        c = config.TDSConfig('foo', '/fake/dir')
        assert c.filename == '/fake/dir/foo'


class TestTDSDatabaseConfig(unittest2.TestCase, FileConfigLoader):
    constructor_kwargs_expected = lambda: [
        (
            dict(access_level='foo'),
            '%s/%s.foo.yml' % (
                config.TDSDatabaseConfig.default_conf_dir,
                config.TDSDatabaseConfig.default_name_fragment
            )
        ),
        (
            dict(access_level='foo', name_fragment='whatever'),
            '%s/whatever.foo.yml' % config.TDSDatabaseConfig.default_conf_dir
        ),
        (
            dict(access_level='foo', conf_dir='/fake/dir'),
            ('/fake/dir/%s.foo.yml' %
                config.TDSDatabaseConfig.default_name_fragment)
        ),
        (
            dict(
                access_level='foo',
                conf_dir='/fake/dir',
                name_fragment='whatever'
            ),
            '/fake/dir/whatever.foo.yml'
        ),

    ]

    @data_provider(constructor_kwargs_expected)
    def test_constructor(self, kwargs, expected):
        c = config.TDSDatabaseConfig(**kwargs)
        assert c.filename == expected

    def test_schema_success(self):
        c = config.TDSDatabaseConfig('foo')
        self.load_fake_config(c, 'dbaccess.test')

        fake_config = tests.factories.config.DatabaseTestConfigFactory()

        assert c['db.user'] == fake_config['db']['user']
        assert c['db.password'] == fake_config['db']['password']

    def test_schema_failure(self):
        c = config.TDSDatabaseConfig('foo')
        self.load_fake_config(c, 'dbaccess.test')
        c['db'].pop('user')
        self.assertRaises(config.ConfigurationError, c.verify, None)


class TestTDSDeployConfig(unittest2.TestCase, FileConfigLoader):
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
        assert c.filename == expected

    def test_schema_success(self):
        c = config.TDSDeployConfig('foo')
        self.load_fake_config(c, 'deploy')
        fake_config = tests.factories.config.DeployConfigFactory()
        assert c == fake_config

    def test_dotted_key_hit(self):
        c = config.TDSDeployConfig('foo')
        self.load_fake_config(c, 'deploy')
        assert c['notifications.hipchat.token'] == 'deadbeef'

    def test_dotted_key_miss(self):
        c = config.TDSDeployConfig('foo')
        self.load_fake_config(c, 'deploy')
        self.assertRaises(KeyError, lambda: c['notifications.hipchat.missing'])

    def test_dotted_key_miss_default(self):
        c = config.TDSDeployConfig('foo')
        self.load_fake_config(c, 'deploy')
        assert 'default' == c.get('notifications.hipchat.missing', 'default')
