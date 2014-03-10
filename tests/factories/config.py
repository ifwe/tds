import tds.utils.config
import factory

from os.path import join
from .. import FIXTURES_PATH


class ConfigFactory(factory.Factory):
    FACTORY_FOR = tds.utils.config.TDSConfig

    conf_dir = join(FIXTURES_PATH, 'config')


class DeployConfigFactory(ConfigFactory):
    FACTORY_FOR = tds.utils.config.TDSDeployConfig


class TestDatabaseConfigFactory(ConfigFactory):
    FACTORY_FOR = tds.utils.config.TDSDatabaseConfig

    access_level = 'test'
