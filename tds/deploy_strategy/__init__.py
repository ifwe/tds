'Different ways to deploy things to Tagged infrastructure'

from .base import DeployStrategy
from .tds_mco import TDSMCODeployStrategy
from .tds_salt import TDSSaltDeployStrategy

__all__ = ['DeployStrategy', 'TDSMCODeployStrategy', 'TDSSaltDeployStrategy']
