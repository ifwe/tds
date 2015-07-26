"""
REST API view for hosts.
"""

from cornice.resource import resource, view

from . import utils
from .base import BaseView, init_view

@resource(collection_path="/hosts", path="/hosts/{name_or_id}")
@init_view(name='hostTarget')
class ApplicationView(BaseView):
    """
    Application view. This object maps to the /hosts and
    /hosts/{name_or_id} URLs.
    An object of this class is initalized to handle each request.
    The collection_* methods correspond to the /hosts URL while the
    others correspond to the /hosts/{name_or_id} URL.
    """

    # JSON types for params.
    types = {
        'id': 'number',
        'name': 'string',
    }

    # URL parameter routes to Python object fields.
    # Params not included are mapped to themselves.
    param_routes = {}

    defaults = {}

    required_post_fields = ("name",)

    @view(validators=('validate_put_post', 'validate_post_required',
                      'validate_cookie'))
    def collection_post(self):
        """
        Handle a POST request after the parameters are marked valid JSON.
        """
        return self._handle_collection_post()
