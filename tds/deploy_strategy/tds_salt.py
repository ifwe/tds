"""Salt-based DeployStrategy."""

import json
import tds.utils

from .base import DeployStrategy

import logging
log = logging.getLogger('tds')

# Note: in order to do multi-host in one call, need to specify them as
# comma-separated string in the first arguent to publish.publish, like:
# 'x.tagged.com,y.tagged.com'
# Then, after all the args to the function call being published, add
# 'expr_form=list'


class TDSSaltDeployStrategy(DeployStrategy):
    """Salt (master publish.publish) based DeployStrategy."""

    def __init__(self, bin=None, user=None, c_dir=None, **kwargs):
        self.bin = bin or 'salt-call'
        self.user = user
        self.c_dir = c_dir

    def _publish(self, host, action, *args):
        """Dispatch to salt master."""

        user_cmd = []

        if self.user is not None:
            user_cmd = ['sudo', '-u', self.user]

        salt_opts = ['--out', 'json']
        if self.c_dir is not None:
            salt_opts += ['-c', self.c_dir]

        salt_cmd = [self.bin, 'publish.publish']
        publish_args = [host, action] + list(args)
        cmd = user_cmd + salt_cmd + salt_opts + publish_args

        proc = tds.utils.processes.run(cmd, expect_return_code=None)

        info = {}
        if proc.stdout:
            try:
                info = json.loads(proc.stdout)
            except ValueError:
                log.error(
                    "Could not decode result from salt. stdout=%r, stderr=%r",
                    proc.stdout, proc.stderr
                )

        return proc.returncode == 0, info

    @tds.utils.debug
    def deploy_to_host(self, dep_host, app, version, retry=4):
        """Deploy an application to a given host"""
        log.debug('Deploying to host %r', dep_host)
        return self._publish(dep_host, 'tds.install', app, version)

    @tds.utils.debug
    def restart_host(self, dep_host, app, retry=4):
        """Restart application on a given host"""
        return self._publish(dep_host, 'tds.restart', app)
