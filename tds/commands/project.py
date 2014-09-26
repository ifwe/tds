"""Commands to manage the TDS projects."""
import logging

from tds.exceptions import AlreadyExistsError
from tds.model import Project
from .base import BaseController, validate

log = logging.getLogger('tds')


class ProjectController(BaseController):

    """Commands to manage TDS projects."""

    @staticmethod
    def create(project, **_kwds):
        """Add a project."""
        project_name = project
        project = Project.get(name=project_name)
        if project is not None:
            raise AlreadyExistsError(
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
    def list(self, projects=(), **_kwds):
        """Show information for requested projects (or all projects)."""
        if len(projects) == 0:
            projects = Project.all()

        return dict(result=projects)
