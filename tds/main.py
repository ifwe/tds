'''
Command and view resolver for TDS.
'''
import getpass
import os
import pwd
import logging

import tds.authorize
import tds.commands
import tds.views
import tds.utils

import tagopsdb
from tds.exceptions import AccessError, ConfigurationError
from tds.model import LocalActor


log = logging.getLogger('tds.main')


class TDS(object):
    """TDS main class"""

    _config = None
    _dbconfig = None
    _authconfig = None

    view = tds.views.CLI

    views = {
        ('jenkinspackage', 'add'): 'package_add',
        ('deploy', 'redeploy'): 'deploy_promote',
        ('config', 'add_apptype'): 'deploy_add_apptype',
        ('config', 'create'): 'project_create',
        ('config', 'delete_apptype'): 'deploy_delete_apptype',
        ('config', 'invalidate'): 'deploy_invalidate',
        ('config', 'push'): 'deploy_promote',
        ('config', 'show'): 'deploy_show',
        ('config', 'validate'): 'deploy_validate',
        ('config', 'repush'): 'deploy_promote',
        ('config', 'revert'): 'deploy_rollback',
        ('repository', 'add'): 'project_create',
        ('repository', 'delete'): 'project_delete',
        ('repository', 'list'): 'project_list',
    }

    def __init__(self, params):
        """Basic initialization"""

        self.params = params
        self.params['deployment'] = True

    @property
    def config(self):
        if self._config is None:
            self._config = self._load_config(self.params)
        return self._config

    @property
    def dbconfig(self):
        if self._dbconfig is None:
            self._dbconfig = self._load_dbconfig(self.params)
        return self._dbconfig

    @property
    def authconfig(self):
        if self._authconfig is None:
            self._authconfig = self._load_authconfig(self.params)
        return self._authconfig

    @staticmethod
    def _load_config(params):
        'Load app config'
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
        'Load database config'
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
    def check_exclusive_options(self):
        """Ensure certain options are exclusive and set parameter
           to check for explicit hosts or application types
        """

        log.debug('Checking certain options are exclusive')

        # Slight hack: ensure only one of '--hosts', '--apptypes'
        # or '--all-apptypes' is used at a given time
        excl = filter(None, (self.params.get('hosts', None),
                             self.params.get('apptypes', None),
                             self.params.get('all_apptypes', None)))

        if len(excl) > 1:
            raise ConfigurationError('Only one of the "--hosts", '
                                     '"--apptypes" or "--all-apptypes" '
                                     'options may be used at a given time')

        if not excl:
            self.params['explicit'] = False
        else:
            self.params['explicit'] = True

        log.log(5, '"explicit" parameter is: %(explicit)s', self.params)

    @tds.utils.debug
    def update_program_parameters(self):
        """Set some additional program parameters"""

        log.debug('Adding several additional parameters for program')

        self.params['user'] = pwd.getpwuid(os.getuid()).pw_name
        log.log(5, 'User is: %s', self.params['user'])

        self.params['user_level'] = self.authconfig.get_access_level(LocalActor())
        log.log(5, 'User level is: %s', self.params['user_level'])

        self.params['environment'] = self.config['env.environment']
        log.log(5, 'Environment is: %s', self.params['environment'])

        self.params['repo'] = self.config['repo']
        self.params['jenkins_url'] = self.config['jenkins.url']

        self.params['package_add_timeout'] = self.config['repo.update_timeout']
        self.params['mco_bin'] = self.config['mco.bin']

        log.log(5, '"repo" parameter values are: %r', self.params['repo'])

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

    @tds.utils.debug
    def execute_command(self):
        """Run the requested command for TDS"""

        log.debug('Running the requested command')
        command = self.params['command_name'].replace('-', '_')
        subcommand = self.params['subcommand_name'].replace('-', '_')
        full_command = (command, subcommand)
        controller_name = command.capitalize() + "Controller"
        log.log(5, 'Instantiating class %r', controller_name)

        view_name = self.views.get(
            full_command,
            '%s_%s' % full_command
        )

        ControllerClass = getattr(tds.commands, controller_name)
        controller = ControllerClass(self.config)

        result = controller.action(subcommand, **self.params)

        return self.render(view_name, result)

    def render(self, *args, **kwargs):
        return self.view(output_format=self.params['output_format']) \
            .generate_result(*args, **kwargs)
