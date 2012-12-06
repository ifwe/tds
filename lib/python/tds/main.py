import getpass
import os
import pwd
import sys

import tds.authorize
import tds.commands
import tds.utils

from tagopsdb.database import init_session
from tagopsdb.exceptions import PermissionsException
from tds.exceptions import AccessError, ConfigurationError, \
                           NotImplementedError, WrongEnvironmentError, \
                           WrongProjectTypeError


class TDS(object):
    """ """

    def __init__(self, args):
        """Basic initialization"""

        self.args = args
        self.log = args.log


    @tds.utils.debug
    def check_user_auth(self):
        """Verify the user is authorized to run the application"""

        self.log.debug('Checking user authorization level')

        self.args.user_level = tds.authorize.get_access_level()
        self.log.debug(5, 'User level is: %s', self.args.user_level)

        if self.args.user_level is None:
            self.log.error('Your account (%s) is not allowed to run this '
                           'application.\nPlease refer to your manager '
                           'for assistance.' % self.args.user)
            sys.exit(1)


    @tds.utils.debug
    def check_exclusive_options(self):
        """Ensure certain options are exclusive and set parameter
           to check for explicit hosts or application types
        """

        self.log.debug('Checking certain options are exclusive')

        # Slight hack: ensure only one of '--hosts', '--apptypes'
        # or '--all-apptypes' is used at a given time
        excl = filter(None, (getattr(self.args, 'hosts', None),
                             getattr(self.args, 'apptypes', None),
                             getattr(self.args, 'all_apptypes', None)))

        if len(excl) > 1:
            self.log.error('Only one of the "--hosts", "--apptypes" or '
                           '"--all-apptypes" options may be used at '
                           'a given time')
            sys.exit(1)

        if not excl:
            self.args.explicit = False
        else:
            self.args.explicit = True

        self.log.debug(5, '"explicit" parameter is: %s', self.args.explicit)


    @tds.utils.debug
    def update_program_parameters(self):
        """Set some additional program parameters"""

        self.log.debug('Adding several additional parameters for program')

        self.args.user = pwd.getpwuid(os.getuid()).pw_name
        self.log.debug(5, 'User is: %s', self.args.user)
        self.check_user_auth()

        self.args.environment = \
            tds.utils.verify_conf_file_section('deploy', 'env')
        self.log.debug(5, 'Environment is: %s', self.args.environment)

        build_base, incoming, processing = \
            tds.utils.verify_conf_file_section('deploy', 'repo')

        self.args.repo = { 'build_base' : build_base,
                           'incoming' : incoming,
                           'processing' : processing, }
        self.log.debug(5, '"repo" parameter values are: %r', self.args.repo)


    @tds.utils.debug
    def initialize_db(self):
        """Get user/password information for the database and connect
           to the database
        """

        self.log.debug('Connecting to the database')

        if self.args.dbuser:
            db_user = self.args.dbuser
            db_password = getpass.getpass('Enter DB password: ')
        else:
            db_user, db_password = \
                tds.utils.verify_conf_file_section('dbaccess', 'db',
                                           sub_cf_name=self.args.user_level)

        self.log.debug(5, 'DB user is: %s, DB password is: %s',
                       db_user, db_password)

        try:
            init_session(db_user, db_password)
        except PermissionsException, e:
            self.log.error('Access issue with database:\n%s' % e)
            sys.exit(1)


    @tds.utils.debug
    def execute_command(self):
        """Run the requested command for TDS"""

        self.log.debug('Running the requested command')

        self.log.debug(5, 'Instantiating class %r',
                       self.args.command_name.capitalize())
        cmd = getattr(tds.commands,
                      self.args.command_name.capitalize())(self.log)

        try:
            self.log.debug(5, 'Executing subcommand %r',
                           self.args.subcommand_name.replace('-', '_'))
            getattr(cmd,
                    self.args.subcommand_name.replace('-', '_'))(self.args)
        except AccessError:
            self.log.error('Your account (%s) does not have the appropriate '
                           'permissions\nto run the requested command.'
                           % args.user)
            sys.exit(1)
        except (ConfigurationError, NotImplementedError,
                WrongEnvironmentError, WrongProjectTypeError), e:
            self.log.error(e)
            sys.exit(1)
