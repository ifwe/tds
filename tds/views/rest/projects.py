"""
REST API view for projects.
"""

from cornice.resource import resource

from .base import BaseView, init_view


@resource(collection_path="/projects", path="/projects/{name_or_id}")
@init_view(name='project')
class ProjectView(BaseView):
    """
    Project view. This object maps to the /projects and /projects/{name_or_id}
    URLs.
    An object of this class is initalized to handle each request.
    The collection_* methods correspond to the /projects URL while the others
    correspond to the /projects/{name_or_id} URL.
    """

    validators = {
        'id': '_validate_unique',
        'name': '_validate_unique',
    }
