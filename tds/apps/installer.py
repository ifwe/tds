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

"""
Daemon to do installs. It checks the database to see what deployments it needs
to do, does them, and updates the database.
"""

import logging
import os
import sys

import time
from datetime import datetime, timedelta

import tagopsdb
import tds.deploy_strategy
import tds.exceptions
import tds.model

if __package__ is None:
    # This unused import is necessary if the file is executed as a script,
    # usually during testing
    import tds.apps
    __package__ = 'tds.apps'

from . import TDSProgramBase

log = logging.getLogger('tds.apps.tds_installer')


class Installer(TDSProgramBase):
    """
    Daemon class that launches new processes to deploy packages to targets.
    """

    def __init__(self, params, *args, **kwargs):
        """
        Determine deployment strategy and initialize some parameters.
        """
        self.retry = params.pop('retry', 4)
        self.deployment_id = params.pop('deployment_id', None)

        super(Installer, self).__init__(params, *args, **kwargs)

        log.info('Initializing database session')
        self.initialize_db()

        self.create_deploy_strategy(
            self.config.get('deploy_strategy', 'salt')
        )

        self.environment = tagopsdb.model.Environment.get(
            env=self.config.get('env', {'environment': 'dev'})['environment']
        )

    def create_deploy_strategy(self, deploy_strat_name):
        """
        Create a deploy strategy and set it to self.deploy_strategy.
        """
        if deploy_strat_name == 'mco':
            cls = tds.deploy_strategy.TDSMCODeployStrategy
        elif deploy_strat_name == 'salt':
            cls = tds.deploy_strategy.TDSSaltDeployStrategy
        else:
            raise tds.exceptions.ConfigurationError(
                'Invalid deploy strategy: %r', deploy_strat_name
            )

        self.deploy_strategy = cls(
            **self.config.get(deploy_strat_name, {})
        )

    def _refresh(self, obj):
        """
        WTF
        """
        tagopsdb.Session.commit()
        obj.refresh()

    @staticmethod
    def get_deployment(dep_id):
        """
        Get a deployment by the given ID.
        """
        return tds.model.Deployment.get(id=dep_id)

    @staticmethod
    def commit_session():
        """
        Commit tagopsdb.Session.
        """
        tagopsdb.Session.commit()

    def find_deployment(self):
        """
        Find host and tier deployments with status == 'queued'.
        Returns the tuple that was appended to ongoing_deployments, False
        otherwise.
        """
        deps = tds.model.Deployment.find(status='queued', order_by='declared')

        while deps:
            deployment = deps[0]
            if any(
                x.environment_id != self.environment.id for x in
                deployment.app_deployments
            ) or any(
                x.host.environment_id != self.environment.id for x in
                deployment.host_deployments
            ):
                deps.pop(0)
                continue
            return deployment

        return None

    def _do_host_deployment(self, host_deployment, first_dep=True):
        """
        Perform host deployment for given host and update database
        with results.
        """
        now = datetime.now()
        # If host already has a valid deployment, nothing to do
        if host_deployment.status == 'ok':
            return 'ok'

        if not first_dep:
            time.sleep(host_deployment.deployment.delay)

        self._refresh(host_deployment.deployment)
        if host_deployment.deployment.status == 'canceled':
            return 'canceled'

        host_deployment.status = 'inprogress'
        tagopsdb.Session.commit()
        success, host_result = self.deploy_strategy.deploy_to_host(
            host_deployment.host.name,
            host_deployment.package.name,
            host_deployment.package.version,
            retry=self.retry
        )

        if success:
            host_deployment.status = 'ok'
        else:
            host_deployment.status = 'failed'
        self._set_duration(host_deployment, now)

        host_deployment.deploy_result = host_result
        tagopsdb.Session.commit()

        return host_deployment.status

    def _do_tier_deployment(self, tier_deployment, first_dep=True):
        """
        Perform tier deployment for given tier (only doing hosts that
        require the deployment) and update database with results.
        """
        now = datetime.now()
        dep_hosts = sorted(
            tier_deployment.application.hosts,
            key=lambda host: host.name,
        )
        tier_state = []

        done_host_dep_ids = set()
        canceled = False
        tier_deployment.status = 'inprogress'
        tagopsdb.Session.commit()
        for dep_host in dep_hosts:
            host_deployment = tds.model.HostDeployment.get(
                host_id=dep_host.id,
                deployment_id=tier_deployment.deployment_id,
            )
            if host_deployment is None:
                continue
            host_state = self._do_host_deployment(host_deployment, first_dep)
            done_host_dep_ids.add(host_deployment.id)
            tier_state.append(host_state)
            if host_state == 'canceled':
                canceled = True
                break
            first_dep = False

        if (canceled and not first_dep) or any(
            x in tier_state for x in ('failed', 'canceled')
        ):
            tier_deployment.status = 'incomplete'
        elif not canceled:
            tier_deployment.status = 'complete'
        self._set_duration(tier_deployment, now)

        tagopsdb.Session.commit()
        return done_host_dep_ids

    def do_serial_deployment(self, deployment):
        """
        Perform deployments for tier or host(s) one host at a time
        (no parallelism).
        """
        now = datetime.now()
        tier_deployments = sorted(
            deployment.app_deployments,
            key=lambda dep:dep.target.name,
        )

        first_dep = True
        done_host_dep_ids = set()
        for tier_deployment in tier_deployments:
            done_host_dep_ids |= self._do_tier_deployment(
                tier_deployment, first_dep
            )
            first_dep = False

            self._refresh(deployment)
            if deployment.status == 'canceled':
                deployment.status = 'stopped'
                self._set_duration(deployment, now)
                tagopsdb.Session.commit()
                return

        host_deployments = sorted(
            [dep for dep in deployment.host_deployments if dep.id not in
             done_host_dep_ids],
            key=lambda host_dep: host_dep.host.name,
        )

        for host_deployment in host_deployments:
            self._do_host_deployment(host_deployment, first_dep)
            first_dep = False

            self._refresh(deployment)
            if deployment.status == 'canceled':
                deployment.status = 'stopped'
                self._set_duration(deployment, now)
                tagopsdb.Session.commit()
                return

        if any(dep.status != 'complete' for dep in tier_deployments) or \
                any(dep.status != 'ok' for dep in deployment.host_deployments):
            deployment.status = 'failed'
        else:
            deployment.status = 'complete'
        self._set_duration(deployment, now)
        tagopsdb.Session.commit()

    @staticmethod
    def _set_duration(deployment, now):
        """
        Set duration of deployment to total float seconds since now.
        deployment should be an object with a duration attribute (deployment,
        host deployment, tier deployment).
        now should be a datetime.
        """
        deployment.duration = (datetime.now() - now).total_seconds()

    def run(self):
        """
        Find a deployment in need of being done, for use if being run as a
        script rather than in tandem with TDSInstallerDaemon.
        """
        if self.deployment_id is not None:
            deployment = tds.model.Deployment.get(id=self.deployment_id)
        else:
            deployment = self.find_deployment()
        if deployment is not None:
            self.do_serial_deployment(deployment)


if __name__ == '__main__':
    def parse_command_line(cl_args):
        """
        Parse command line and return dict.
        """
        # TODO implement parser thing?
        # Be sure to pass '--config-dir' for testing
        try:
            int(cl_args[-1])
        except ValueError:
            return {
                'config_dir': cl_args[-1],
            }
        else:
            return {
                'deployment_id': cl_args[-1],
            }
    parsed_args = parse_command_line(sys.argv[1:])
    parsed_args['user_level'] = 'admin'

    if 'config_dir' in parsed_args:
        logfile = os.path.join(parsed_args['config_dir'], 'tds_installer.log')
    else:
        logfile = '/var/log/tds_installer.log'
        # 'logger' set at top of program
        log = logging.getLogger('')

    log.setLevel(logging.DEBUG)
    handler = logging.FileHandler(logfile, 'a')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s",
                                  "%b %e %H:%M:%S")
    handler.setFormatter(formatter)
    log.addHandler(handler)

    prog = Installer(parsed_args)
    prog.run()
