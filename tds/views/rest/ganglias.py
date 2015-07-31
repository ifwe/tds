"""
REST API view for Ganglia objects.
"""

from cornice.resource import resource, view

import tagopsdb
from .base import BaseView, init_view

@resource(collection_path="/ganglias", path="/ganglias/{name_or_id}")
@init_view(name="ganglia", model=tagopsdb.model.Ganglia)
class GangliaView(BaseView):
    """
    Ganglia view. This object maps to the /ganglias and /ganglias/{name_or_id} URLs.
    An object of this class is initialized to handle each request.
    The collection_* methods correspond to the /ganglia URL while the others
    correspond to the /ganglias/{name_or_id} URL.
    """

    # JSON types for params.
    types = {
        'id': 'integer',
        'name': 'string',
        'port': 'integer',
    }

    # URL parameter routes to Python object fields.
    # Params not included are mapped to themselves.
    param_routes = {
        'name': 'cluster_name',
    }

    defaults = {}

    required_post_fields = ("name",)

    def validate_ganglia_post(self, _request):
        """
        Validate a post request.
        """
        self._validate_id("POST")
        self._validate_name("POST")

    def validate_ganglia_put(self):
        """
        Validate a PUT request.
        """
        self._validate_id("PUT")
        self._validate_name("PUT")

    @view(validators=('validate_put_post', 'validate_post_required',
                      'validate_ganglia_post', 'validate_cookie'))
    def collection_post(self):
        """
        Handle a POST request after the parameters are marked valid JSON.
        """
        return self._handle_collection_post()
