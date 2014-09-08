"""Model module for deployment target object."""

from .base import Base
from .project import Project
import tagopsdb


class DeployTarget(Base):
    """
    A deploy target is something that can be deployed to
    examples:
        host
        apptype
        a list of hosts or apptypes
    """
    # name / app_type
    # distribution
    # host_base
    # puppet_class
    # ganglia
    # ganglia_group_name  # XXX: this should be part of ganglia object
    # app_deployments
    # hipchats
    # hosts
    # host_specs
    # applications (aka package_definitions)
    # nag_app_services
    # nag_host_services
    # package_definitions
    # projects
    #

    # TODO: make subclasses where only one is an AppDefinition


class AppTarget(DeployTarget):
    """An application target."""

    delegate = tagopsdb.AppDefinition

    @property
    def projects(self):
        """Return list of projects for this AppTarget."""
        return [Project(delegate=p) for p in self.delegate.projects]


class HostTarget(DeployTarget):
    """A host target."""

    delegate = tagopsdb.Host

    @property
    def hosts(self):
        return [self]

    @property
    def application(self):
        return AppTarget(delegate=self.delegate.application)
