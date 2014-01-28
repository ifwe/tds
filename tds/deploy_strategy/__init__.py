class DeployStrategy(object):
    def deploy_to_host(self, dep_host, app, version, retry=4):
        raise NotImplementedError


    def restart_host(self, dep_host, app, retry=4):
        raise NotImplementedError

from .tds_mco import TDSMCODeployStrategy

__all__ = ['DeployStrategy', 'TDSMCODeployStrategy']
