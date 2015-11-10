"""Model module for deployment object."""

import tagopsdb

from .base import Base
from .application import Application
from .deploy_target import AppTarget


class Deployment(Base):
    """Model class for deployment object."""

    delegate = tagopsdb.Deployment


class AppDeployment(Deployment):
    """Model class for deployment of an application to a tier."""

    delegate = tagopsdb.AppDeployment

    @property
    def application(self):
        return Application(delegate=self.delegate.package.application)

    def get_incomplete_host_deployments(self):
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
        return AppTarget(delegate=self.delegate.host.target)

    @property
    def host_state(self):
        return self.delegate.host.state

    @property
    def application(self):
        return Application(delegate=self.delegate.package.application)
