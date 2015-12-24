"""
Daemon to do installs. It checks the database to see what deployments it needs
to do, does them, and updates the database.
"""

import logging
import os
import sys

import time
from datetime import datetime, timedelta
from multiprocessing import Process

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

    def __init__(self, *args, **kwargs):
        """
        Determine deployment strategy and initialize some parameters.
        """
        # ongoing_deployments is a dict with ID keys and values of form:
        # (deployment_entry, process_doing_deployment,
        #  time_of_deployment_start)
        self.ongoing_deployments = dict()
        self.retry = kwargs.pop('retry') if 'retry' in kwargs else 4
        self.threshold = kwargs.pop('threshold') if 'threshold' in kwargs \
            else timedelta(minutes=5)

        super(Installer, self).__init__(*args, **kwargs)

        log.info('Initializing database session')
        self.initialize_db()

        self.create_deploy_strategy(
            self.config.get('deploy_strategy', 'salt')
        )

        self.environment = tagopsdb.model.Environment.get(
            env=self.config.get('env', {'environment': 'dev'})['environment']
        )

    def create_deploy_strategy(self, deploy_strat_name):
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

    def find_deployments(self):
        """
        Find host and tier deployments with status == 'queued'.
        Returns the tuple that was appended to ongoing_deployments, False
        otherwise.
        """

        deps = tds.model.Deployment.find(status='queued')

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
            deployment.status = 'inprogress'
            tagopsdb.Session.commit()
            deployment_process = Process(
                target=self.do_serial_deployment,
                args=(deployment,),
            )
            tup = (
                deployment,
                deployment_process,
                datetime.now(),
            )
            self.ongoing_deployments[deployment.id] = tup
            deployment_process.start()

            return tup

        return False

    def get_stalled_deployments(self):
        """
        Return the list of ongoing deployments that were started more than
        self.threshold ago.
        """

        return [dep for dep in self.ongoing_deployments.itervalues()
                if datetime.now() > dep[2] + self.threshold]

    def _do_host_deployment(self, host_deployment, first_dep=True):
        """
        Perform host deployment for given host and update database
        with results.
        """

        # If host already has a valid deployment, nothing to do
        if host_deployment.status == 'ok':
            return 'ok'

        tagopsdb.Session.refresh(host_deployment.deployment)
        if host_deployment.deployment.status == 'canceled':
            return 'canceled'

        if not first_dep:
            time.sleep(host_deployment.deployment.delay)

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

        host_deployment.deploy_result = host_result
        tagopsdb.Session.commit()

        return host_deployment.status

    def _do_tier_deployment(self, tier_deployment, first_dep=True):
        """
        Perform tier deployment for given tier (only doing hosts that
        require the deployment) and update database with results.
        """

        dep_hosts = sorted(
            tier_deployment.application.hosts,
            key=lambda host: host.name,
        )
        tier_state = []

        for dep_host in dep_hosts:
            host_deployment = tds.model.HostDeployment.get(
                host_id=dep_host.id,
                deployment_id=tier_deployment.deployment_id,
            )
            host_state = self._do_host_deployment(host_deployment, first_dep)
            tier_state.append(host_state)
            if host_state == 'canceled':
                return
            first_dep = False

        if any(x in tier_state for x in ('failed', 'canceled')):
            tier_deployment.status = 'incomplete'
        else:
            tier_deployment.status = 'complete'

        tagopsdb.Session.commit()

    def do_serial_deployment(self, deployment):
        """
        Perform deployments for tier or host(s) one host at a time
        (no parallelism).
        """
        tier_deployments = sorted(
            deployment.app_deployments,
            key=lambda dep:dep.target.name,
        )

        first_dep = True
        for tier_deployment in tier_deployments:
            self._do_tier_deployment(tier_deployment, first_dep)
            first_dep = False

            tagopsdb.Session.refresh(deployment)
            if deployment.status == 'canceled':
                deployment.status = 'stopped'
                tagopsdb.Session.commit()
                return

        host_deployments = sorted(
            [dep for dep in deployment.host_deployments if dep.status ==
             'pending'],
            key=lambda host_dep: host_dep.host.name,
        )

        for host_deployment in host_deployments:
            self._do_host_deployment(host_deployment, first_dep)
            first_dep = False

            tagopsdb.Session.refresh(deployment)
            if deployment.status == 'canceled':
                deployment.status = 'stopped'
                return

        if any(dep.status != 'complete' for dep in tier_deployments) or \
                any(dep.status != 'ok' for dep in deployment.host_deployments):
            deployment.status = 'failed'
        else:
            deployment.status = 'complete'
        tagopsdb.Session.commit()

        del self.ongoing_deployments[deployment.id]

    def run(self):
        """
        Find a deployment in need of being done (which spawns a process
        that handles the actual deployment)
        """

        self.find_deployments()


if __name__ == '__main__':
    def parse_command_line(cl_args):
        # TODO implement parser thing?
        return {
            'config_dir': cl_args[1]
        }
    args = parse_command_line(sys.argv[1:])

    log.setLevel(logging.DEBUG)
    logfile = os.path.join(args['config_dir'], 'tds_installer.log')
    handler = logging.FileHandler(logfile, 'a')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s",
                                  "%b %e %H:%M:%S")
    handler.setFormatter(formatter)
    log.addHandler(handler)

    prog = Installer(args)
    prog.run()
