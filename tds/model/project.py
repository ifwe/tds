'''Model module for project object'''

from .base import Base
import tagopsdb


class TDSProject(Base, tagopsdb.Project):
    'A project links applications together in a deployable group'
    # name
    # type
    # applications (aka package_definitions)

    @property
    def applications(self):
        return self.package_definitions

# For sqlalchemy class lookup
Project = TDSProject
