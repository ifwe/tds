'''Model module for application object'''

from .base import Base
import tagopsdb


class Application(Base):
    'Represents a single application'
    delegate = tagopsdb.PackageDefinition
    # name
    # path
    # build_host
    # environment
    # packages / versions

    @classmethod
    def from_db(cls, row):
        return cls(
            name=row.pkg_name,
            path=row.path,
            build_host=row.build_host,
            environment_specific=row.env_specific,
            target_groups=[app.app_type for app in row.applications]
        )
