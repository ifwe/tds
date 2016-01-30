"""
REST API view for projects.
"""

from cornice.resource import resource

from .base import BaseView, init_view
from .urls import ALL_URLS
from .permissions import PROJECT_PERMISSIONS


@resource(collection_path=ALL_URLS['project_collection'],
          path=ALL_URLS['project'])
@init_view(name='project')
class ProjectView(BaseView):
    """
    Project view. This object maps to the /projects and /projects/{name_or_id}
    URLs.
    An object of this class is initalized to handle each request.
    The collection_* methods correspond to the /projects URL while the others
    correspond to the /projects/{name_or_id} URL.
    """

    required_post_fields = ('name',)

    permissions = PROJECT_PERMISSIONS

    individual_allowed_methods = dict(
        GET=dict(description="Get project matching name or ID."),
        PUT=dict(description="Update project matching name or ID."),
    )

    collection_allowed_methods = dict(
        GET=dict(description="Get a list of projects, optionally by limit and/"
                 "or start."),
        POST=dict(description="Add a new project."),
    )
