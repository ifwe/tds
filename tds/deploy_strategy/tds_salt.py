"""Salt based DeployStrategy"""

import salt.client
import tds.utils

from .base import DeployStrategy

import logging
log = logging.getLogger('tds')


class TDSSaltDeployStrategy(DeployStrategy):
    """Salt (master publish.publish) based DeployStrategy"""

    @staticmethod
    def _publish(host, cmd, app):
        """dispatch to salt master"""
        caller = salt.client.Caller()
        return caller.function('publish.publish', host, cmd, app)

    @tds.utils.debug
    def deploy_to_host(self, dep_host, app, version, retry=4):
        """Deploy an application to a given host"""
        log.debug('Deploying to host %r', dep_host)
        return self._publish(dep_host, 'tds_cmd.install', app)

    @tds.utils.debug
    def restart_host(self, dep_host, app, retry=4):
        """Restart application on a given host"""
        return self._publish(dep_host, 'tds_cmd.restart', app)