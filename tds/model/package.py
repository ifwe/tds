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

    def check_app_deployments(self, tier, environment):
        """
        Check for an existing validated deployment for a given tier
        and environment; this is just a boolean check
        """

        for dep in self.delegate.deployments:
            for app_dep in dep.app_deployments:
                if (app_dep.target == tier.delegate and
                    app_dep.environment_obj == environment and
                    app_dep.status == 'validated'):
                    return True

        return False

    # Note: this is currently not used but is left here for possible
    # inclusion or future reference - KEL 20150825
    def find_app_deployments(self, tier, environment):
        """Find app deployments for a given tier and environment"""

        from .deployment import AppDeployment

        for dep in self.delegate.deployments:
            for app_dep in dep.app_deployments:
                if (app_dep.target == tier.delegate and
                    app_dep.environment_obj == environment):
                    yield AppDeployment(delegate=app_dep)
