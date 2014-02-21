import mock
import unittest2

import yaml
import tds.utils.config as config

fake_config = {
    'env': {'environment': 'fakedev'},
    'logging': {
        'syslog_facility': 'fakelocal3',
        'syslog_priority': 'fakedebug'
    },
    'notifications': {
        'email_receiver': 'fake@example.com',
        'enabled_methods': ['fake'],
        'hipchat_rooms': ['fakeroom'],
        'hipchat_token': 'deadbeef',
        'validation_time': -1
    },
    'repo': {
        'build_base': '/fake/mnt/deploy/builds',
        'incoming': '/fake/mnt/deploy/incoming',
        'processing': '/fake/mnt/deploy/processing'
    }
}


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
    def load_fake_config(self, c):
        m = mock.mock_open(read_data=yaml.dump(fake_config))
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
            self.load_fake_config(c)

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
