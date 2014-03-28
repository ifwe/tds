
import salt.client
import tds.utils
import tds.scripts.tds_install as tds_install

from .base import DeployStrategy

import logging
logger = logging.getLogger('tds')


class TDSSaltDeployStrategy(DeployStrategy):

    @tds.utils.debug
    def deploy_to_host(self, dep_host, app, version, retry=4):
        caller = salt.client.Caller()
        logger.debug('Deploying to host %r', dep_host)
        return caller.function('publish.publish', dep_host,
                               'tds_install.install', app)

    @tds.utils.debug
    def restart_host(self, dep_host, app, retry=4):
        """Restart application on a given host"""
        caller = salt.client.Caller()
        return caller.function('publish.publish', dep_host,
                               'tds_install.restart', app)
