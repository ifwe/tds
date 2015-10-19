"""Notify about unvalidated deployments."""

import argparse
import sys

import tds.utils.config
import tds.version

from tds.utils.script_helpers import (
    UnvalidatedDeploymentNotifier,
    TagopsdbDeploymentProvider,
    ValidationMonitor
)


def parse_command_line(sysargs):
    """Parse the command line and return the parser to the main program."""

    parser = argparse.ArgumentParser(description='TDS Unvalidated Check')

    parser.add_argument('-V', '--version', action='version',
                        version='TDS Unvalidated Check %s'
                        % tds.version.__version__)
    parser.add_argument('-v', '--verbose', action='count',
                        help='Show more information (more used shows greater '
                             'information)')
    parser.add_argument('--config-dir',
                        help='Specify directory containing app config',
                        default='/etc/tagops/')

    return parser.parse_args(sysargs)


def main():
    """
    Load config, create ValidationMonitor instance, and process notifications.
    """

    args = parse_command_line(sys.argv[1:])

    config = tds.utils.config.TDSDeployConfig(conf_dir=args['config_dir'])
    db_config = tds.utils.config.TDSDatabaseConfig('admin', 'tagopsdb')

    config.load()
    db_config.load()

    dep_provider = TagopsdbDeploymentProvider(db_config)
    vmon = ValidationMonitor(config, dep_provider)
    notifier = UnvalidatedDeploymentNotifier(config)

    dep_provider.init()
    notifier.notify(vmon.get_deployments_requiring_validation())

    return 0

if __name__ == '__main__':
    sys.exit(main())
