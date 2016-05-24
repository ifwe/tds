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

"""Commands to manage the TDS projects."""
import logging

import tds.exceptions
from tds.model import Project
from .base import BaseController, validate

log = logging.getLogger('tds')


class ProjectController(BaseController):
    """Commands to manage TDS projects."""

    access_levels = dict(
        list='environment',
        add='admin',
        delete='admin',
    )

    @staticmethod
    def add(project, **_kwds):
        """Add a project."""
        project_name = project
        project = Project.get(name=project_name)
        if project is not None:
            raise tds.exceptions.AlreadyExistsError(
                "Project already exists: %s", project.name
            )

        log.debug('Creating project %r', project_name)
        return dict(result=Project.create(name=project_name))

    @validate('project')
    def delete(self, project, **_kwds):
        """Remove a given project."""
        log.debug('Removing project %r', project.name)
        project.delete()
        return dict(result=project)

    @validate('project')
    def list(self, applications=(), projects=(), **_kwds):
        """Show information for requested projects (or all projects)."""
        if len(projects) == 0:
            projects = Project.all()

        return dict(result=projects)
