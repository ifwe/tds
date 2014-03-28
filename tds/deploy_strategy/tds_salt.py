
import salt.client
import tds.utils
import tds.scripts.tds_install as tds_install

from .base import DeployStrategy

import logging
logger = logging.getLogger('tds')


class TDSSaltDeployStrategy(DeployStrategy):

    def _publish(self, host, cmd, app):
        caller = salt.client.Caller()
        return caller.function('publish.publish', host, cmd, app)

    @tds.utils.debug
    def deploy_to_host(self, dep_host, app, version, retry=4):
        logger.debug('Deploying to host %r', dep_host)
        return self._publish(dep_host, 'tds_install.install', app)

    @tds.utils.debug
    def restart_host(self, dep_host, app, retry=4):
        """Restart application on a given host"""
        return self._publish(dep_host, 'tds_install.restart', app)
