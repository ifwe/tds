"""Model module for deployment object."""

import tagopsdb

from .base import Base
from .application import Application
from .deploy_target import AppTarget


class Deployment(Base):
    """Model class for deployment object."""

    # TO FIX: Can't use a delegate here right now due to
    # the 'convert_deployment' method in tds/utils/script_helpers.py
    # Once that's fixed, this can be enabled
    #delegate = tagopsdb.Deployment


class AppDeployment(Deployment):
    """Model class for deployment of an application to a tier."""

    delegate = tagopsdb.AppDeployment

    @property
    def application(self):
        """
        Return the application of the package that is deployed with this tier
        deployment.
        """
        return Application(delegate=self.delegate.package.application)

    def get_incomplete_host_deployments(self):
        """
        Get all incomplete host deployments associated with this tier
        deployment (and therefore also associated with its deployment).
        """
        return tagopsdb.Session.query(tagopsdb.model.HostDeployment).join(
            tagopsdb.model.HostDeployment.host
        ).filter(
            tagopsdb.model.HostDeployment.deployment_id == self.deployment_id,
            tagopsdb.model.Host.app_id == self.app_id,
            tagopsdb.model.HostDeployment.status.in_(
                ('inprogress', 'failed', 'pending')
            ),
        ).all()


class HostDeployment(Deployment):
    """Model class for deployment of an application to a host."""

    delegate = tagopsdb.HostDeployment

    @property
    def app_target(self):
        """
        Return the tier of the host target of this host deployment.
        """
        return AppTarget(delegate=self.delegate.host.target)

    @property
    def host_state(self):
        """
        Return the host state of the host target of this host deployment.
        """
        return self.delegate.host.state

    @property
    def application(self):
        """
        Return the application of the package that is deployed with this host
        deployment.
        """
        return Application(delegate=self.delegate.package.application)
