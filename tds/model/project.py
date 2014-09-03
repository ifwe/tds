"""Model module for project object."""

from .base import Base
import tagopsdb


class Project(Base):
    """A project links applications together in a deployable group."""
    # name
    # applications (aka package_definitions)

    delegate = tagopsdb.Project

    @property
    def applications(self):
        """Alias for package_definitions."""
        return self.package_definitions

    @property
    def targets(self):
        """Return deploy targets, but ignore the "dummy" target."""
        from .deploy_target import AppTarget
        return [
            AppTarget(delegate=x)
            for x in self.delegate.targets
            if x.name != x.dummy
        ]
