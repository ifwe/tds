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

'''
Factories for tds.util.config classes. They are backed by files in
tests/fixtures/config.
'''

import tds.authorize
import tds.utils.config
import factory

from os.path import join
from tests import FIXTURES_PATH


class ConfigFactory(factory.Factory):
    """Superclass to redirect to tests/fixtures/config directory."""
    FACTORY_FOR = tds.utils.config.TDSConfig

    conf_dir = join(FIXTURES_PATH, 'config')

    __loaded = factory.PostGenerationMethodCall('load')


class DeployConfigFactory(ConfigFactory):
    """A factory for a config that uses deploy.yml."""
    FACTORY_FOR = tds.utils.config.TDSDeployConfig


class DatabaseTestConfigFactory(ConfigFactory):
    """A factory for a config that uses dbaccess.%(access_level)s.yml."""
    FACTORY_FOR = tds.utils.config.TDSDatabaseConfig

    access_level = 'test'
    base_name_fragment = 'tagopsdb'


class AuthConfigFactory(factory.Factory):
    """A factory for TDSAuthConfig."""
    FACTORY_FOR = tds.authorize.TDSAuthConfig
    filename = join(FIXTURES_PATH, 'config', 'auth.yml')
    __loaded = factory.PostGenerationMethodCall('load')
