'''Model module for project object'''

from .base import Base
from .application import Application
from tagopsdb import Project as DBProject


class Project(Base):
    'A project links applications together in a deployable group'
    # name
    # type
    # applications

    delegate = DBProject

    @classmethod
    def from_db(cls, row):
        return cls(row,
            name=row.name,
            applications=map(Application.from_db, row.package_definitions),
        )
