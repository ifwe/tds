'Different ways to deploy things to Tagged infrastructure'

from .base import DeployStrategy
from .tds_mco import TDSMCODeployStrategy

__all__ = ['DeployStrategy', 'TDSMCODeployStrategy']
