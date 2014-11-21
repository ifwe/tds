'Notify about unvalidated deployments'

import sys

import tds.utils.config

from ..utils.script_helpers import (
    UnvalidatedDeploymentNotifier,
    TagopsdbDeploymentProvider,
    ValidationMonitor
)


def main():
    '''
    Load config, create ValidationMonitor instance, and process notifications
    '''

    config = tds.utils.config.TDSDeployConfig()
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
