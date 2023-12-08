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

"""Program to run a daemon on yum repository servers to manage
   new packages being added to the deploy repository for TDS.
"""

import logging
import time
import signal

import tds.apps

from . import TDSDaemon

log = logging.getLogger('update_deploy_repo')


class UpdateDeployRepoDaemon(TDSDaemon):
    """Daemon to manage updating the deploy repository with new packages."""

    def __init__(self, app, **kwargs):
        super(UpdateDeployRepoDaemon, self).__init__(app)
        self.zookeeper_path = '/tdsdeployrepo'

        # Set up callbacks.
        def loop_callback():
            time.sleep(1.0)

        def run_callback():
            self.app.run()

        self.loop_callback = loop_callback
        self.run_callback = run_callback


def daemon_main():
    """Prepare logging then initialize daemon."""

    logfile = '/var/log/update_deploy_repo.log'

    # 'logger' set at top of program
    rootlog = logging.getLogger('')
    rootlog.setLevel(logging.DEBUG)
    handler = logging.FileHandler(logfile, 'a')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s",
                                  "%b %e %H:%M:%S")
    handler.setFormatter(formatter)
    rootlog.addHandler(handler)
    logging.getLogger('kazoo').propagate = False

    app = tds.apps.RepoUpdater(dict(
        user_level='admin',
    ))

    daemon = UpdateDeployRepoDaemon(app)

    signal.signal(signal.SIGINT, daemon.shutdown_handler)
    signal.signal(signal.SIGTERM, daemon.shutdown_handler)

    daemon.run()


if __name__ == '__main__':
    daemon_main()
