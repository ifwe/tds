"""Model module for package object."""

from .base import Base
import tagopsdb


class Package(Base):
    """Represents a deployable package for a version of an application."""
    # name
    # version
    # application

    delegate = tagopsdb.Package

    def check_app_deployments(self, tier, environment):
        """
        Check for an existing validated deployment for a given tier
        and environment; this is just a boolean check
        """

        for app_dep in self.delegate.app_deployments:
            if (app_dep.target == tier.delegate and
                app_dep.environment_obj.env == environment and
                app_dep.status == 'validated'):
                return True

        return False

    # Note: this is currently not used but is left here for possible
    # inclusion or future reference - KEL 20150825
    def find_app_deployments(self, tier, environment):
        """Find app deployments for a given tier and environment"""

        from .deployment import AppDeployment

        for app_dep in self.delegate.app_deployments:
            if (app_dep.target == tier.delegate and
                app_dep.environment_obj == environment):
                yield AppDeployment(delegate=app_dep)

    def get_current_app_deployment(self, tier_id, environment_id, query=None):
        if query is None:
            query = tagopsdb.Session.query(tagopsdb.model.AppDeployment)
        return query.filter(
            tagopsdb.model.AppDeployment.package_id == self.id,
            tagopsdb.model.AppDeployment.app_id == tier_id,
            tagopsdb.model.AppDeployment.environment_id == environment_id,
        ).order_by(desc(tagopsdb.model.AppDeployment.realized)).first()
