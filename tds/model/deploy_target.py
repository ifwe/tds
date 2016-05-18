# Copyright 2016 Ifwe Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Model module for deployment target object."""

import tagopsdb

from .base import Base
from .application import Application
from .project import Project


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

    @property
    def hosts(self):
        """
        Return all hosts associated with this tier.
        """
        return [HostTarget(delegate=x) for x in self.delegate.hosts]

    def remove_application(self, application, project=None):
        if project is not None:
            projects = [project]
        else:
            projects = self.projects

        for project in projects:
            proj_pkg = tagopsdb.ProjectPackage.get(
                project_id=project.id,
                pkg_def_id=application.id,
                app_id=self.id
            )

            if proj_pkg is None:
                continue

            proj_pkg.delete()

        tagopsdb.Session.commit()

    def get_ongoing_deployments(self, environment_id, query=None):
        """
        Return all ongoing tier deployments on this tier in the environment
        with ID environment_id.
        """
        if query is None:
            query = tagopsdb.Session.query(tagopsdb.model.AppDeployment)
        return query.join(tagopsdb.model.AppDeployment.deployment).filter(
            tagopsdb.model.AppDeployment.app_id == self.id,
            tagopsdb.model.AppDeployment.environment_id == environment_id,
            tagopsdb.model.AppDeployment.status.in_(('pending', 'inprogress')),
            tagopsdb.model.Deployment.status.in_(('queued', 'inprogress')),
        ).all()

    def get_ongoing_host_deployments(self, environment_id, query=None):
        """
        Return all ongoing host deployments for hosts associated with this tier
        in the environment with ID environment_id
        """
        if query is None:
            query = tagopsdb.Session.query(tagopsdb.model.HostDeployment)
        return query.join(tagopsdb.model.HostDeployment.deployment).join(
            tagopsdb.model.HostDeployment.host
        ).filter(
            tagopsdb.model.Host.app_id == self.id,
            tagopsdb.model.Host.environment_id == environment_id,
            tagopsdb.model.HostDeployment.status.in_(
                ('pending', 'inprogress')
            ),
            tagopsdb.model.Deployment.status.in_(('queued', 'inprogress')),
        ).all()


class HostTarget(DeployTarget):
    """A host target."""

    delegate = tagopsdb.Host

    @property
    def hosts(self):
        """
        Return a list containing just this host.
        Convenience property to mirror AppTarget.hosts property.
        """
        return [self]

    @property
    def application(self):
        """
        Return own tier.
        """
        return AppTarget(delegate=self.delegate.application)

    @property
    def package_definitions(self):
        """
        Return all applications associated with this.
        """
        return [Application(delegate=x)
                for x in self.target.package_definitions]

    def get_ongoing_deployments(self, query=None):
        """
        Return all ongoing deployments on this host.
        """
        if query is None:
            query = tagopsdb.Session.query(tagopsdb.model.HostDeployment)
        return query.join(tagopsdb.model.HostDeployment.host).filter(
            tagopsdb.model.HostDeployment.id == self.id,
            tagopsdb.model.HostDeployment.status.in_(
                ('pending', 'inprogress')
            ),
            tagopsdb.model.Deployment.status.in_(('queued', 'inprogress')),
        ).all()
