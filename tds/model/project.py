'''Model module for project object'''

from .base import Base
from .deploy_target import DeployTarget
import tagopsdb


class Project(Base):
    'A project links applications together in a deployable group'
    # name
    # applications (aka package_definitions)

    delegate = tagopsdb.Project

    @property
    def applications(self):
        'Alias for package_definitions'
        return self.package_definitions

    @property
    def environment_specific(self):
        '''
        Returns False iff there are applications and at least
        one is env specific
        '''
        return all((not x.environment_specific) for x in self.applications)

    @property
    def targets(self):
        'Return deploy targets, but ignore the "dummy" target'
        return [
            DeployTarget(delegate=x)
            for x in self.delegate.targets
            if x.name != x.dummy
        ]
