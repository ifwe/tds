"""Model module for deployment object."""

from .base import Base
import tagopsdb


class Deployment(Base):
    """Model class for deployment object."""

    @property
    def application(self):
        return self.delegate.deployment.package.application


class AppDeployment(Deployment):
    """Model class for deployment of an application to a tier."""

    delegate = tagopsdb.AppDeployment


class HostDeployment(Deployment):
    """Model class for deployment of an application to a host."""

    delegate = tagopsdb.HostDeployment

    @property
    def app_target(self):
        return self.delegate.host.target

    @property
    def host_state(self):
        return self.delegate.host.state
