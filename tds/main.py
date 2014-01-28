import getpass
import os
import pwd

import tds.authorize
import tds.commands
import tds.utils

from tagopsdb.database import init_session
from tagopsdb.exceptions import PermissionsException
from tds.exceptions import AccessError, ConfigurationError


class TDS(object):
    """ """

    def __init__(self, params):
        """Basic initialization"""

        self.params = params
        self.params['deployment'] = True
        self.log = params['log']


    @tds.utils.debug
    def check_user_auth(self):
        """Verify the user is authorized to run the application"""

        self.log.debug('Checking user authorization level')

        self.params['user_level'] = tds.authorize.get_access_level()
        self.log.debug(5, 'User level is: %s', self.params['user_level'])

        if self.params['user_level'] is None:
            raise AccessError('Your account (%s) is not allowed to run this '
                              'application.\nPlease refer to your manager '
                              'for assistance.' % self.params['user'])


    @tds.utils.debug
    def check_exclusive_options(self):
        """Ensure certain options are exclusive and set parameter
           to check for explicit hosts or application types
        """

        self.log.debug('Checking certain options are exclusive')

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

        self.log.debug(5, '"explicit" parameter is: %s',
                       self.params['explicit'])


    @tds.utils.debug
    def update_program_parameters(self):
        """Set some additional program parameters"""

        self.log.debug('Adding several additional parameters for program')

        self.params['user'] = pwd.getpwuid(os.getuid()).pw_name
        self.log.debug(5, 'User is: %s', self.params['user'])
        self.check_user_auth()

        self.params['environment'] = \
            tds.utils.verify_conf_file_section('deploy', 'env')
        self.log.debug(5, 'Environment is: %s', self.params['environment'])

        build_base, incoming, processing = \
            tds.utils.verify_conf_file_section('deploy', 'repo')

        self.params['repo'] = { 'build_base' : build_base,
                                'incoming' : incoming,
                                'processing' : processing, }
        self.log.debug(5, '"repo" parameter values are: %r',
                       self.params['repo'])


    @tds.utils.debug
    def initialize_db(self):
        """Get user/password information for the database and connect
           to the database
        """

        self.log.debug('Connecting to the database')

        if self.params.get('dbuser', None):
            db_user = self.params['dbuser']
            db_password = getpass.getpass('Enter DB password: ')
        else:
            db_user, db_password = \
                tds.utils.verify_conf_file_section('dbaccess', 'db',
                                      sub_cf_name=self.params['user_level'])

        self.log.debug(5, 'DB user is: %s, DB password is: %s',
                       db_user, db_password)

        try:
            init_session(db_user, db_password)
        except PermissionsException, e:
            raise AccessError('Access issue with database:\n%s' % e)


    @tds.utils.debug
    def execute_command(self):
        """Run the requested command for TDS"""

        self.log.debug('Running the requested command')

        self.log.debug(5, 'Instantiating class %r',
                       self.params['command_name'].capitalize())
        cmd = getattr(tds.commands,
                      self.params['command_name'].capitalize())(self.log)

        try:
            self.log.debug(5, 'Executing subcommand %r',
                           self.params['subcommand_name'].replace('-', '_'))
            getattr(cmd,
                self.params['subcommand_name'].replace('-', '_'))(self.params)
        except:
            raise   # Just pass error up to top level
