'Commands to manage the TDS projects'
import logging

from tds.model import Project

log = logging.getLogger('tds')


class ProjectController(object):

    """Commands to manage TDS projects"""

    def __init__(self, config):
        super(ProjectController, self).__init__()
        self.app_config = config

    @staticmethod
    def create(project, **_kwds):
        """Add a project"""
        project_name = project
        project = Project.get(name=project_name)
        if project is not None:
            return dict(error=Exception(
                "Project already exists: %s", project.name
            ))

        log.debug('Creating project %r', project_name)
        return dict(result=Project.create(name=project_name))

    @staticmethod
    def delete(project, **_kwds):
        """Remove a given project"""

        project_name = project
        project = Project.get(name=project_name)
        if project is None:
            return dict(error=Exception(
                'Project "%s" does not exist', project_name
            ))

        log.debug('Removing project %r', project_name)

        project.delete()
        return dict(result=project)

    @staticmethod
    def list(projects=(), **_kwds):
        """Show information for requested projects (or all projects)"""
        project_names = projects

        if project_names:
            return dict(
                result=filter(
                    None,
                    [Project.get(name=p)
                     or Exception('Project "%s" does not exist', p)
                     for p in project_names]
                )
            )
        else:
            return dict(result=Project.all())
