"""
REST API view for projects.
"""

from cornice.resource import resource, view

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

    types = {
        'id': 'number',
        'name': 'string',
    }

    required_post_fields = ('name',)

    def validate_proj_post(self, _request):
        """
        Validate a POST request by preventing collisions over name.
        """
        self._validate_id("POST")
        self._validate_name("POST")

    def validate_project_put(self):
        """
        Validate a PUT request by preventing collisions over unique fields.
        """
        self._validate_id("PUT")
        self._validate_name("PUT")

    @view(validators=('validate_put_post', 'validate_post_required',
                      'validate_proj_post', 'validate_cookie'))
    def collection_post(self):
        """
        Handle a POST request after the parameters are marked valid JSON.
        """
        return self._handle_collection_post()
