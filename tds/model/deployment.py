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
