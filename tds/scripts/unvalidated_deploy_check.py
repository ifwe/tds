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

"""Notify about unvalidated deployments."""

import argparse
import logging
import sys

import tds.utils.config
import tds.version

from tds.utils.script_helpers import (
    UnvalidatedDeploymentNotifier,
    TagopsdbDeploymentProvider,
    ValidationMonitor
)

logging.basicConfig()
log = logging.getLogger('tds')


def parse_command_line(sysargs):
    """Parse the command line and return the parser to the main program."""

    parser = argparse.ArgumentParser(description='TDS Unvalidated Check')

    parser.add_argument('-V', '--version', action='version',
                        version='TDS Unvalidated Check %s'
                        % tds.version.__version__)
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='Show more information (more used shows greater '
                             'information)')
    parser.add_argument('--auth-config',
                        help='Specify authorization config file',
                        default=None)
    parser.add_argument('--config-dir',
                        help='Specify directory containing app config',
                        default='/etc/tagops/')

    return parser.parse_args(sysargs)


def main():
    """
    Load config, create ValidationMonitor instance, and process notifications.
    """

    args = parse_command_line(sys.argv[1:])

    log_levels = [
        logging.INFO,
        logging.WARNING,
        logging.DEBUG,
    ]
    log_level_idx = min(args.verbose, len(log_levels) - 1)
    log.setLevel(log_levels[log_level_idx])

    config = tds.utils.config.TDSDeployConfig(conf_dir=args.config_dir)
    db_config = tds.utils.config.TDSDatabaseConfig('admin', 'tagopsdb',
                                                   conf_dir=args.config_dir)

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
