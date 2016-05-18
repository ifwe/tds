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

"""Salt-based DeployStrategy."""

import os

import salt.client
import salt.config

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

    def __init__(self, c_dir=None):
        self.c_dir = c_dir

    @tds.utils.debug
    def _publish(self, host, cmd, *args):
        """Dispatch to salt master."""

        if self.c_dir is not None:
            opts = salt.config.minion_config(
                os.path.join(self.c_dir, 'minion')
            )
        else:
            opts = salt.config.minion_config('/etc/salt.tds/minion')

        caller = salt.client.Caller(mopts=opts)
        host_re = '%s.*' % host   # To allow FQDN matching

        # Set timeout high because... RedHat
        result = caller.sminion.functions['publish.full_data'](
            host_re, cmd, args, timeout=120
        )

        if not result:
            return (False, 'No data returned from host %s' % host)

        # We're assuming only one key is being returned currently
        host_result = result.values()[0]['ret']
        success = host_result.endswith('successful')

        return (success, host_result)

    @tds.utils.debug
    def deploy_to_host(self, dep_host, app, version, retry=4):
        """Deploy an application to a given host"""

        log.debug('Deploying to host %r', dep_host)
        return self._publish(dep_host, 'tds.install', app, version)

    @tds.utils.debug
    def restart_host(self, dep_host, app, retry=4):
        """Restart application on a given host"""

        return self._publish(dep_host, 'tds.restart', app)
