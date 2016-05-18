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
Base class for TDS applications. Mostly in charge of
DB initialization and loading config
'''

import getpass
import logging

import tagopsdb

import tds.utils.config

log = logging.getLogger('tds.apps.base')


class TDSProgramBase(object):
    '''
    Base class for a program in the TDS ecosystem. Loads configs and stuff
    '''

    _config = None
    _dbconfig = None
    _authconfig = None

    def __init__(self, params):
        self.params = params

    @property
    def config(self):
        """Return configuration."""
        if self._config is None:
            self._config = self._load_config(self.params)
        return self._config

    @property
    def dbconfig(self):
        """Return database configuration."""
        if self._dbconfig is None:
            self._dbconfig = self._load_dbconfig(self.params)
        return self._dbconfig

    @property
    def authconfig(self):
        """Return auth configuration."""
        if self._authconfig is None:
            self._authconfig = self._load_authconfig(self.params)
        return self._authconfig

    @staticmethod
    def _load_config(params):
        """Load app config."""
        config = tds.utils.config.TDSDeployConfig(
            conf_dir=params.get(
                'config_dir',
                tds.utils.config.TDSDatabaseConfig.default_conf_dir
            )
        )
        config.load()

        return config

    @staticmethod
    def _load_dbconfig(params):
        """Load database config."""
        dbconfig = tds.utils.config.TDSDatabaseConfig(
            params.get('user_level', 'dev'),
            base_name_fragment='tagopsdb',
            conf_dir=params.get(
                'config_dir',
                tds.utils.config.TDSDatabaseConfig.default_conf_dir
            )
        )
        dbconfig.load()
        return dbconfig

    @staticmethod
    def _load_authconfig(params):
        """Load auth config."""
        authconfig = tds.authorize.TDSAuthConfig(
            params.get('auth_config', '/etc/tagops/tds_auth.yml')
        )
        authconfig.load()
        return authconfig

    @tds.utils.debug
    def initialize_db(self):
        """Get user/password information for the database and connect
           to the database
        """

        log.debug('Connecting to the database')

        if self.params.get('dbuser', None):
            db_user = self.params['dbuser']
            db_password = getpass.getpass('Enter DB password: ')
        else:
            db_user = self.dbconfig['db.user']
            db_password = self.dbconfig['db.password']

        tagopsdb.init(
            url=dict(
                username=db_user,
                password=db_password,
                host=self.dbconfig['db.hostname'],
                database=self.dbconfig['db.db_name'],
            ),
            pool_recycle=3600
        )
