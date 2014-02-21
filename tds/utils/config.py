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

log = logging.getLogger('tds.util.config')


class DottedDict(dict):
    """Allow dictionary keys to be accessed like attributes"""

    sentinel = object()

    def __getitem__(self, key, default=sentinel):
        """ """

        key_parts = key.split('.')
        d = self

        while key_parts:
            part = key_parts.pop(0)
            try:
                d = dict.__getitem__(d, part)
            except KeyError as e:
                if default is type(self).sentinel:
                    raise e
                else:
                    return default

        return d


class Config(DottedDict):
    """Base configuration class"""

    @debug
    def load(self, logger):
        """Abstract method, must be defined in subclasses"""

        raise NotImplementedError


class FileConfig(Config):
    """General configuration file handling"""

    def __init__(self, filename):
        """ """

        super(FileConfig, self).__init__()
        self.filename = filename

    @debug
    def load(self, logger=None):
        """Read information from configuration file and update"""

        log.debug('Loading configuration file %r', self.filename)

        try:
            with open(self.filename) as f:
                data = f.read()
        except IOError as e:
            raise ConfigurationError('Unable to read configuration file '
                                     '%r: %s', self.filename, e)

        self.update(self.parse(data))

    @debug
    def parse(self, data):
        """Abstract method, must be defined in subclasses"""

        raise NotImplementedError


class YAMLConfig(FileConfig):
    """YAML configuration file handling"""

    @debug
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

    @debug
    def verify(self, logger=None):
        """Verify data, loading it in first if necessary"""

        if not len(self):
            self.load(logger)

        type(self)._verify(self, self.schema, logger)

    @staticmethod
    @debug
    def _verify(data, schema, logger=None):
        """Data verification - ensure all entries are correct
        and complete
        """

        for key in schema:
            schema_keys = schema.get(key, [])

            log.debug(
                5, 'Checking for config keys %r in section %r',
                schema_keys, key
            )

            data_keys = data.get(key, [])
            noncompliant_keys = set(schema_keys) ^ set(data_keys)

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

        self.filename = os.path.join(conf_dir, filename)


class TDSDatabaseConfig(TDSConfig):
    """Handle TDS database configuration file"""

    default_name_fragment = 'dbaccess'
    schema = {
        'db': ['user', 'password', ],
    }

    def __init__(self, access_level, name_fragment=default_name_fragment,
                 conf_dir=TDSConfig.default_conf_dir):
        """ """

        super(TDSDatabaseConfig, self).__init__(
            '%s.%s.yml' % (name_fragment, access_level), conf_dir=conf_dir
        )


class TDSDeployConfig(TDSConfig):
    """Handle TDS deployment configuration file"""

    default_name_fragment = 'deploy'
    schema = {
        'env': ['environment', ],
        'logging': ['syslog_facility', 'syslog_priority', ],
        'notifications': ['enabled_methods', 'email_receiver',
                          'hipchat_rooms', 'hipchat_token',
                          'validation_time', ],
        'repo': ['build_base', 'incoming', 'processing', ],
    }

    def __init__(self, name_fragment=default_name_fragment,
                 conf_dir=TDSConfig.default_conf_dir):
        """ """

        super(TDSDeployConfig, self).__init__('%s.yml' % (name_fragment,),
                                              conf_dir=conf_dir)


# deprecated
@debug
def verify_conf_file_section(cf_name, section, sub_cf_name=None):
    """Ensure the given section in the given configuration file
    is valid and complete and return values
    """

    logger = logging.getLogger('tds')

    conf_factory = {
        'deploy': lambda: TDSDeployConfig(),
        'dbaccess': lambda: TDSDatabaseConfig(sub_cf_name),
    }.get(cf_name, None)

    if conf_factory is None:
        raise Exception("Unknown config file requested: %r", cf_name)

    conf = conf_factory()
    conf.load(logger=logger)
    conf.verify(logger=logger)

    logger.debug(5, 'Data is: %r', conf)

    values = [conf.get(section, {}).get(x) for x in conf.schema.get(section)]
    if len(values) == 1:
        return values[0]

    return values
