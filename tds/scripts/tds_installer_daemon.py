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
        self.ongoing_deployments = list()
        self.threshold = timedelta(minutes=5)
        super(TDSInstallerDaemon, self).__init__(*args, **kwargs)

    def find_deployments(self):
        """
        Find host and tier deployments with status == 'queued'.
        """
        deps = tds.model.Deployment.find(started=False)
        if deps:
            deployment = deps[0]
            deployment_process = Process(
                target=self.do_serial_deployment,
                args=(host_deployment,),
            )
            self.ongoing_deployments.append((
                deployment,
                deployment_process,
                datetime.now(),
            ))

    def get_stalled_deployments(self):
        """
        Return the list of ongoing deployments that were started more than
        self.threshold ago.
        """
        return [dep for dep in self.ongoing_deployments
                if datetime.now() > dep[2] + self.threshold]

    def _do_host_deployment(self, host_deployment):
        pass

    def _do_tier_deployment(self, deployment, tier_deployment):
        pass

    def do_serial_deployment(self, deployment):
        tier_deployments = deployment.app_deployments
        if tier_deployments:
            for tier_deployment in  tier_deployments:
                self._do_tier_deployment(self, deployment, tier_deployment)
        else:
            host_deployments = deployment.host_deployments
            for host_deployment in host_deployments:
                self._do_host_deployment(host_deployment)
