'''Main file for TDS application'''

import argparse
import sys

import argcomplete

import tds.cmdline
import tds.configure_logging as conflog
import tds.version

from tds.exceptions import AccessError, ConfigurationError, \
    WrongEnvironmentError, WrongProjectTypeError


def create_subparsers(parser):
    """Generate the subparsers to use for the command line"""

    data = tds.cmdline.parser_info()

    cmd_parsers = parser.add_subparsers(dest='command_name',
                                        help='command help')

    for cmd, cmd_data in data.iteritems():
        cmd_parser = cmd_parsers.add_parser(cmd)

        subparsers = cmd_parser.add_subparsers(dest='subcommand_name',
                                               help='subcommand help')

        for subcmd, subcmd_data in cmd_data.iteritems():
            subcmd_parser = subparsers.add_parser(subcmd,
                                                  help=subcmd_data['help'])

            for args, kwargs in subcmd_data['subargs'].iteritems():
                subcmd_parser.add_argument(*args, **kwargs)


def parse_command_line(sysargs):
    """Parse the command line and return the parser to the main program"""

    parser = argparse.ArgumentParser(description='TagOps Deployment System')

    parser.add_argument('-V', '--version', action='version',
                        version='TDS %s' % tds.version.__version__)
    parser.add_argument('-v', '--verbose', action='count',
                        help='Show more information (more used shows greater '
                             'information)')
    parser.add_argument('--dbuser',
                        help='Specify user to use to connect to database',
                        default=None)
    parser.add_argument('--disable-color', dest='use_color',
                        action='store_false',
                        help='Disable color coding when in verbose mode(s)')
    parser.add_argument('--auth-config',
                        help='Specify authorization config file',
                        default=None)
    parser.add_argument('--config-dir',
                        help='Specify directory containing app config',
                        default='/etc/tagops/')

    create_subparsers(parser)
    argcomplete.autocomplete(parser)

    return parser.parse_args(sysargs)


def _main(sysargs):
    """Parse command line, configure logging and initialize application,
       then run specified command
    """
    args = parse_command_line(sysargs)
    tds_params = vars(args)
    for k in tds_params.keys():
        if tds_params[k] is None:
            tds_params.pop(k)

    tds_params['log'] = conflog.configure_logging(
        tds_params['config_dir'],
        tds_params.get('verbose', None),
        tds_params['use_color']
    )
    tds_params['log'].debug(5, 'Program parameters: %r',
                            sorted(tds_params.iteritems()))

    # Must be done *after* logging is configured
    import tds.main as tds_main

    prog = tds_main.TDS(tds_params)

    try:
        prog.check_exclusive_options()
        prog.update_program_parameters()
        prog.initialize_db()
        prog.execute_command()
    except (AccessError, ConfigurationError, NotImplementedError,
            WrongEnvironmentError, WrongProjectTypeError) as exc:
        tds_params['log'].error(exc)
        sys.exit(1)


def main():
    'Wrapper around _main() that passes in sys.argv'
    return _main(sys.argv[1:])


if __name__ == '__main__':
    main()
