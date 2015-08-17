"""
Daemon to do installs. It checks the database to see what deployments it needs
to do, does them, and updates the database.
"""

from datetime import datetime, timedelta
from multiprocessing import Process

import tds

from simpledaemon import Daemon


class TDSInstallerDaemon(Daemon):
    """
    Thing to do the thing.
    """

    def __init__(self, *args, **kwargs):
        # A list with items of form:
        # (deployment_entry, process_doing_deployment,
        #  time_of_deployment_start)
        self.retry = kwargs.pop('retry') if 'retry' in kwargs else 4
        self.ongoing_deployments = list()
        self.threshold = kwargs.pop('threshold') if 'threshold' in kwargs \
            else timedelta(minutes=5)
        super(TDSInstallerDaemon, self).__init__(*args, **kwargs)

    def find_deployments(self):
        """
        Find host and tier deployments with status == 'queued'.
        Returns the tuple that was appended to ongoing_deployments, False
        otherwise.
        """
        deps = tds.model.Deployment.find(started=False)
        if deps:
            deployment = deps[0]
            deployment_process = Process(
                target=self.do_serial_deployment,
                args=(deployment,),
            )
            tup = (
                deployment,
                deployment_process,
                datetime.now(),
            )
            self.ongoing_deployments.append(tup)
            return tup
        return False

    def get_stalled_deployments(self):
        """
        Return the list of ongoing deployments that were started more than
        self.threshold ago.
        """
        return [dep for dep in self.ongoing_deployments
                if datetime.now() > dep[2] + self.threshold]

    def _do_host_deployment(self, host_deployment):
        success, host_result = self.deploy_strategy.deploy_to_host(
            host_deployment.host.name,
            host_deployment.deployment.package.name,
            host_deployment.deployment.package.version,
            retry=self.retry
        )
        if success:
            host_deployment.status = 'ok'
        else:
            host_deployment.status = 'failed'
        if len(host_result) <= 255:
            host_deployment.deploy_result = host_result
        else:
            host_deployment.deploy_result = host_result[0:255]
        tagopsdb.Session.commit()

    def _do_tier_deployment(self, deployment, tier_deployment):
        pass

    def do_serial_deployment(self, deployment):
        tier_deployments = deployment.app_deployments
        if tier_deployments:
            for tier_deployment in  tier_deployments:
                self._do_tier_deployment(self, deployment, tier_deployment)
        else:
            host_deployments = sorted(
                deployment.host_deployments,
                key=lambda host_dep: host_dep.host.name,
            )
            for host_deployment in host_deployments:
                self._do_host_deployment(host_deployment)
