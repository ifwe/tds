"""Model module for package object."""

from .base import Base
import tagopsdb


class Package(Base):
    """Represents a deployable package for a version of an application."""
    # name
    # version
    # application

    delegate = tagopsdb.Package

    @property
    def app_deployments(self):
        """Determine all app deployments related to a given package"""

        from .deployment import AppDeployment
        return [
            AppDeployment(delegate=x)
            for dep in self.delegate.deployments
            for x in dep.app_deployments
        ]
