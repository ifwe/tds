"""
Daemon to do installs. It checks the database to see what deployments it needs
to do, does them, and updates the database.
"""

import logging
import os
import sys

import time
from datetime import datetime, timedelta
from multiprocessing import Process, Manager

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
        self.info_manager = Manager()
        # ongoing_deployments is a dict with ID keys and values of form:
        # [deployment_id, time_of_deployment_start, finished_boolean]
        self.ongoing_deployments = self.info_manager.dict()

        # ongoing_processes is a dict with deployment ID keys and values
        # pointing to the process running that deployment
        self.ongoing_processes = dict()
        self.retry = kwargs.pop('retry') if 'retry' in kwargs else 4
        self.threshold = kwargs.pop('threshold') if 'threshold' in kwargs \
            else timedelta(minutes=30)

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
            self.ongoing_deployments[deployment.id] = self.info_manager.list([
                deployment.id, datetime.now(), False
            ])
            self.ongoing_processes[deployment.id] = deployment_process
            deployment_process.start()

            return tup

        return False

    def clean_up_processes(self):
        """
        Join processes that have finished and terminate stalled processes.
        """
        to_delete = list()
        # Join all done deployment processes
        for dep_id in self.ongoing_deployments:
            if self.ongoing_deployments[dep_id][-1] == True:
                self.ongoing_processes[dep_id].join()
                to_delete.append(dep_id)
        for done_dep_id in to_delete:
            del self.ongoing_processes[done_dep_id]
            del self.ongoing_deployments[done_dep_id]

        # Halt all deployments taking too long.
        for stalled_dep_id, _start, _done in self.get_stalled_deployments():
            proc = self.ongoing_processes[stalled_dep_id]
            proc.terminate()
            proc.join()
            dep = tds.model.Deployment.get(id=stalled_dep_id)
            self._refresh(dep)
            dep.status = 'failed'
            tagopsdb.session.commit()
            del self.ongoing_processes[stalled_dep_id]
            del self.ongoing_deployments[stalled_dep_id]

    def get_stalled_deployments(self):
        """
        Return the list of ongoing deployments that were started more than
        self.threshold ago.
        """
        return [dep for dep in self.ongoing_deployments.itervalues()
                if datetime.now() > dep[1] + self.threshold]

    def _do_host_deployment(self, host_deployment, first_dep=True):
        """
        Perform host deployment for given host and update database
        with results.
        """
        # If host already has a valid deployment, nothing to do
        if host_deployment.status == 'ok':
            return 'ok'

        if not first_dep:
            time.sleep(host_deployment.deployment.delay)

        self._refresh(host_deployment.deployment)
        if host_deployment.deployment.status == 'canceled':
            return 'canceled'

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

        done_host_dep_ids = set()
        canceled = False
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

        tagopsdb.Session.commit()
        return done_host_dep_ids

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
        done_host_dep_ids = set()
        for tier_deployment in tier_deployments:
            done_host_dep_ids |= self._do_tier_deployment(
                tier_deployment, first_dep
            )
            first_dep = False

            self._refresh(deployment)
            if deployment.status == 'canceled':
                deployment.status = 'stopped'
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
                tagopsdb.Session.commit()
                return

        if any(dep.status != 'complete' for dep in tier_deployments) or \
                any(dep.status != 'ok' for dep in deployment.host_deployments):
            deployment.status = 'failed'
        else:
            deployment.status = 'complete'
        tagopsdb.Session.commit()

        self.ongoing_deployments[deployment.id][-1] = True

    def run(self):
        """
        Find a deployment in need of being done (which spawns a process
        that handles the actual deployment)
        """
        self.find_deployments()
        self.clean_up_processes()


if __name__ == '__main__':
    def parse_command_line(cl_args):
        """
        Parse command line and return dict.
        """
        # TODO implement parser thing?
        return {
            'config_dir': cl_args[1]
        }
    parsed_args = parse_command_line(sys.argv[1:])

    log.setLevel(logging.DEBUG)
    logfile = os.path.join(parsed_args['config_dir'], 'tds_installer.log')
    handler = logging.FileHandler(logfile, 'a')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s",
                                  "%b %e %H:%M:%S")
    handler.setFormatter(formatter)
    log.addHandler(handler)

    prog = Installer(parsed_args)
    prog.run()
