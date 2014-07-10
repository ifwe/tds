'''Model module for project object'''

from .base import Base
from tagopsdb import Project as DBProject


class Project(Base, DBProject):
    'A project links applications together in a deployable group'
    # name
    # type
    # applications (aka package_definitions)

    @property
    def applications(self):
        return self.package_definitions
