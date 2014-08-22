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

    command_map = {
        ('config', 'add-apptype'): 'exec_config_add_apptype',
        ('config', 'create'): 'exec_config_create',
        ('config', 'delete-apptype'): 'exec_config_delete_apptype',
        ('config', 'invalidate'): 'exec_config_invalidate',
        ('config', 'push'): 'exec_config_push',
        ('config', 'show'): 'exec_config_show',
        ('config', 'validate'): 'exec_config_validate',
        ('config', 'repush'): 'exec_deploy_redeploy',
        ('config', 'revert'): 'exec_deploy_rollback',
        ('deploy', 'add-apptype'): 'exec_deploy_add_apptype',
        ('deploy', 'delete-apptype'): 'exec_deploy_delete_apptype',
        ('deploy', 'invalidate'): 'exec_deploy_invalidate',
        ('deploy', 'promote'): 'exec_deploy_promote',
        ('deploy', 'redeploy'): 'exec_deploy_redeploy',
        ('deploy', 'restart'): 'exec_deploy_restart',
        ('deploy', 'rollback'): 'exec_deploy_rollback',
        ('deploy', 'show'): 'exec_deploy_show',
        ('deploy', 'validate'): 'exec_deploy_validate',
        ('jenkinspackage', 'add'): 'exec_jenkinspackage_add',
        ('package', 'add'): 'exec_package_add',
        ('package', 'delete'): 'exec_package_delete',
        ('package', 'list'): 'exec_package_list',
        ('project', 'create'): 'exec_project_create',
        ('project', 'delete'): 'exec_project_delete',
        ('project', 'list'): 'exec_project_list',
        ('repository', 'add'): 'exec_repository_add',
        ('repository', 'delete'): 'exec_project_delete',
        ('repository', 'list'): 'exec_project_list',
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
        'Load auth config'
        authconfig = tds.authorize.TDSAuthConfig(
            params.get('auth_config', '/etc/tagops/tds_auth.yml')
        )
        authconfig.load()
        return authconfig

    @tds.utils.debug
    def check_user_auth(self):
        """Verify the user is authorized to run the application"""

        log.debug('Checking user authorization level')

        self.params['user_level'] = self.authconfig.get_access_level(LocalActor())
        log.log(5, 'User level is: %s', self.params['user_level'])

        if self.params['user_level'] is None:
            raise AccessError('Your account (%s) is not allowed to run this '
                              'application.\nPlease refer to your manager '
                              'for assistance.' % self.params['user'])

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
        self.check_user_auth()

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
        command = (self.params['command_name'], self.params['subcommand_name'])
        handler_name = self.command_map.get(command, None)
        if handler_name is None:
            handler_name = 'exec_command_default'
        handler = getattr(self, handler_name, None)

        if handler is None:
            self.exec_command_default()
        else:
            handler()

    def exec_command_default(self):

        log.log(5, 'Instantiating class %r',
                self.params['command_name'].capitalize())

        cmd = getattr(tds.commands,
                      self.params['command_name'].capitalize())(log)

        try:
            log.log(5, 'Executing subcommand %r',
                    self.params['subcommand_name'].replace('-', '_'))
            getattr(
                cmd,
                self.params['subcommand_name'].replace('-', '_')
            )(self.params)
        except:
            raise   # Just pass error up to top level

    def exec_project_list(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.ProjectController,
            action='list',
            view='project_list',
            access_level='dev'
        )

    def exec_project_delete(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.ProjectController,
            action='delete',
            view='project_delete',
            access_level='admin'
        )

    def exec_project_create(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.ProjectController,
            action='create',
            view='project_create',
            access_level='admin'
        )

    def exec_repository_add(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.RepositoryController,
            action='add',
            view='project_create',
            access_level='admin'
        )

    def exec_config_create(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.ConfigController,
            action='create',
            view='project_create',
            access_level='admin'
        )

    def exec_deploy_add_apptype(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.DeployController,
            action='add_apptype',
            view='deploy_add_apptype',
            access_level='admin'
        )

    def exec_config_add_apptype(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.ConfigController,
            action='add_apptype',
            view='deploy_add_apptype',
            access_level='admin'
        )

    def exec_deploy_delete_apptype(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.DeployController,
            action='delete_apptype',
            view='deploy_delete_apptype',
            access_level='admin'
        )

    def exec_config_delete_apptype(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.ConfigController,
            action='delete_apptype',
            view='deploy_delete_apptype',
            access_level='admin'
        )

    def exec_deploy_invalidate(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.DeployController,
            action='invalidate',
            view='deploy_invalidate',
            access_level=self.params['environment']
        )

    def exec_config_invalidate(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.ConfigController,
            action='invalidate',
            view='deploy_invalidate',
            access_level=self.params['environment']
        )

    def exec_deploy_show(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.DeployController,
            action='show',
            view='deploy_show',
            access_level=self.params['environment']
        )

    def exec_config_show(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.ConfigController,
            action='show',
            view='deploy_show',
            access_level=self.params['environment']
        )

    def exec_deploy_validate(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.DeployController,
            action='validate',
            view='deploy_validate',
            access_level=self.params['environment']
        )

    def exec_config_validate(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.ConfigController,
            action='validate',
            view='deploy_invalidate',
            access_level=self.params['environment']
        )

    def exec_jenkinspackage_add(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.JenkinspackageController,
            action='add',
            view='package_add',
            access_level='dev'
        )

    def exec_config_push(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.ConfigController,
            action='push',
            view='deploy_promote',
            access_level=self.params['environment']
        )

    def exec_deploy_promote(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.DeployController,
            action='promote',
            view='deploy_promote',
            access_level=self.params['environment']
        )

    def exec_package_add(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.PackageController,
            action='add',
            view='package_add',
            access_level='dev'
        )

    def exec_package_delete(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.PackageController,
            action='delete',
            view='package_delete',
            access_level='dev'
        )

    def exec_package_list(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.PackageController,
            action='list',
            view='package_list',
            access_level='dev'
        )

    def exec_deploy_redeploy(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.DeployController,
            action='redeploy',
            view='deploy_promote',
            access_level=self.params['environment']
        )

    def exec_deploy_restart(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.DeployController,
            action='restart',
            view='deploy_restart',
            access_level=self.params['environment']
        )

    def exec_deploy_rollback(self):
        return self.exec_controller_default(
            ControllerClass=tds.commands.DeployController,
            action='rollback',
            view='deploy_rollback',
            access_level=self.params['environment']
        )

    def exec_controller_default(self, ControllerClass, action, view, access_level=None):
        if access_level is not None:
            tds.authorize.verify_access(
                self.params.get('user_level', 'disabled'),
                access_level
            )

        controller = ControllerClass(self.config)
        result = getattr(controller, action)(**self.params)

        return self.render(view, result)

    def render(self, *args, **kwargs):
        return self.view().generate_result(*args, **kwargs)
