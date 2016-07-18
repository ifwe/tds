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

'Configuration types and helpers for TDS'
import collections
import os.path
import logging
import yaml

from tds.exceptions import ConfigurationError

from .debug import debug

__all__ = [
    'DottedDict', 'Config', 'FileConfig', 'YAMLConfig',
    'VerifyingConfig', 'TDSConfig', 'TDSDatabaseConfig',
    'TDSDeployConfig'
]

log = logging.getLogger('tds.utils.config')


def update_recurse(mapping, update):
    '''
    Descend through keypaths of 'update', updating the mapping when scalar
    values are found
    '''
    for key, val in update.iteritems():
        if isinstance(val, collections.Mapping):
            mapping[key] = update_recurse(mapping.get(key, {}), val)
        else:
            mapping[key] = val
    return mapping


class DottedDict(dict):
    """Allow dictionary keys to be accessed like attributes"""

    sentinel = object()

    def __getitem__(self, key, default=sentinel):
        """ """

        key_parts = key.split('.')
        mapping = self

        while key_parts:
            part = key_parts.pop(0)
            try:
                mapping = dict.__getitem__(mapping, part)
            except KeyError as e:
                if default is type(self).sentinel:
                    raise e
                else:
                    return default

        return mapping


class Config(DottedDict):
    """Base configuration class"""

    def load(self):
        """Abstract method, must be defined in subclasses"""

        raise NotImplementedError


class FileConfig(Config):
    """General configuration file handling"""

    def __init__(self, filename):
        """ """

        super(FileConfig, self).__init__()
        self.filename = filename

    def load(self):
        """Read information from configuration file and update"""

        log.debug('Loading configuration file %r', self.filename)

        try:
            with open(self.filename) as fobj:
                data = fobj.read()
        except IOError as e:
            raise ConfigurationError('Unable to read configuration file '
                                     '%r: %s', self.filename, e)

        self.update(self.parse(data))

    def parse(self, data):
        """Abstract method, must be defined in subclasses"""

        raise NotImplementedError


class YAMLConfig(FileConfig):
    """YAML configuration file handling"""

    def parse(self, data):
        """Parse YAML data and ensure it's valid"""

        try:
            parsed = yaml.load(data)

            if not isinstance(parsed, dict):
                raise TypeError
        except yaml.error.YAMLError as e:
            raise ConfigurationError('YAML parse error: %s', e)
        except TypeError as e:
            raise ConfigurationError('YAML document should be an associative '
                                     'array, was: %s', type(parsed))

        return parsed


class VerifyingConfig(Config):
    """Verify/validate data in configuration files"""

    schema = {}

    def load(self):
        super(VerifyingConfig, self).load()
        self.verify()

    def verify(self):
        """Verify data, loading it in first if necessary"""

        if not len(self):
            self.load()

        self._verify(self, self.schema)

    @staticmethod
    def _verify(data, schema):
        """Data verification - ensure all entries are correct
        and complete
        """

        for key in schema:
            schema_keys = set(schema.get(key, []))

            log.log(
                5, 'Checking for config keys %r in section %r',
                schema_keys, key
            )

            try:
                data_keys = set(data.get(key, []))
            except TypeError:
                raise ConfigurationError(
                    "Section %r does not contain any keys,"
                    "only found %r", key, data.get(key, [])
                )

            noncompliant_keys = set(schema_keys) ^ data_keys

            if len(noncompliant_keys) == 0:
                continue

            raise ConfigurationError(
                'keys in %r section should be %r, but were %r. offending '
                'keys: %r', key, schema_keys, data_keys, noncompliant_keys
            )


class TDSConfig(YAMLConfig, VerifyingConfig):
    """Base class to handle TDS configuration files"""

    default_conf_dir = '/etc/tagops'

    def __init__(self, filename, conf_dir=default_conf_dir):
        """ """
        super(TDSConfig, self).__init__(os.path.join(conf_dir, filename))


class TDSDatabaseConfig(TDSConfig):
    """Handle TDS database configuration file"""

    default_name_fragment = 'dbaccess'
    schema = {
        'db': ['user', 'password', ],
    }

    def __init__(
        self,
        access_level,
        base_name_fragment,
        name_fragment=default_name_fragment,
        conf_dir=TDSConfig.default_conf_dir
    ):
        """ """

        self.basic = TDSConfig(
            '%s.yml' % (base_name_fragment,),
            conf_dir=conf_dir
        )
        self.access = TDSConfig(
            '%s.%s.yml' % (name_fragment, access_level),
            conf_dir=conf_dir
        )
        super(TDSDatabaseConfig, self).__init__(self.access.filename,
                                                conf_dir=conf_dir)

    def load(self):
        self.basic.load()
        update_recurse(self, self.basic)
        try:
            self.access.load()
        except ConfigurationError:
            pass
        else:
            update_recurse(self, self.access)


class TDSDeployConfig(TDSConfig):
    """Handle TDS deployment configuration file"""

    default_name_fragment = 'deploy'
    schema = {
        'env': ['environment', ],
        'logging': ['syslog_facility', 'syslog_priority', ],
        'notifications': ['enabled_methods', 'email',
                          'hipchat', 'validation_time', ],
        'repo': ['build_base', 'incoming', 'processing', ],
    }

    def __init__(self, name_fragment=default_name_fragment,
                 conf_dir=TDSConfig.default_conf_dir):
        """ """

        super(TDSDeployConfig, self).__init__('%s.yml' % (name_fragment,),
                                              conf_dir=conf_dir)
