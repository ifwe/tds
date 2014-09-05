"""Model module for application object."""

from .base import Base
import tagopsdb


class Application(Base):
    """Represents a single application."""
    # name
    # path
    # build_host
    # environment
    # packages / versions

    delegate = tagopsdb.PackageDefinition

    @property
    def targets(self):
        """Return deploy targets, but ignore the "dummy" target."""
        from .deploy_target import AppTarget
        return [
            AppTarget(delegate=x)
            for x in self.delegate.targets
            if x.name != x.dummy
        ]
