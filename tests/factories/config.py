'''
Factories for tds.util.config classes. They are backed by files in
tests/fixtures/config.
'''

import tds.utils.config
import factory

from os.path import join
from .. import FIXTURES_PATH


class ConfigFactory(factory.Factory):
    'Superclass to redirect to tests/fixtures/config directory'
    FACTORY_FOR = tds.utils.config.TDSConfig

    conf_dir = join(FIXTURES_PATH, 'config')

    __loaded = factory.PostGenerationMethodCall('load')


class DeployConfigFactory(ConfigFactory):
    'A factory for a config that uses deploy.yml'
    FACTORY_FOR = tds.utils.config.TDSDeployConfig


class DatabaseTestConfigFactory(ConfigFactory):
    'A factory for a config that uses dbaccess.%(access_level)s.yml'
    FACTORY_FOR = tds.utils.config.TDSDatabaseConfig

    access_level = 'test'
