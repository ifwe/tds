"""
REST API view for applications.
"""

from cornice.resource import resource, view

import tagopsdb

from .base import BaseView, init_view


@resource(collection_path="/applications", path="/applications/{name_or_id}")
@init_view(name='application')
class ApplicationView(BaseView):
    """
    Application view. This object maps to the /applications and
    /applications/{name_or_id} URLs.
    An object of this class is initalized to handle each request.
    The collection_* methods correspond to the /applications URL while the
    others correspond to the /applications/{name_or_id} URL.
    """

    # JSON types for params.
    types = {
        'id': 'integer',
        'name': 'string',
        'job': 'string',
        'build_host': 'string',
        'build_type': 'choice',
        'deploy_type': 'string',
        'arch': 'choice',
        'validation_type': 'string',
        'env_specific': 'boolean',
    }

    # URL parameter routes to Python object fields.
    # Params not included are mapped to themselves.
    param_routes = {
        'name': 'pkg_name',
        'job': 'path',
    }

    defaults = {
        'arch': 'noarch',
        'build_type': 'jenkins',
        'build_host': 'build_host',
        'deploy_type': 'rpm',
        'validation_type': 'matching',
    }

    required_post_fields = ("name", "job")

    def validate_app_post(self, _request):
        """
        Validate a POST request by preventing collisions over unique fields and
        verifying that arch and build_type are acceptable.
        """
        self._validate_id("POST")
        self._validate_name("POST")

    @view(validators=('validate_put_post', 'validate_post_required',
                      'validate_app_post', 'validate_cookie'))
    def collection_post(self):
        """
        Handle a POST request after the parameters are marked valid JSON.
        """
        return self._handle_collection_post()
