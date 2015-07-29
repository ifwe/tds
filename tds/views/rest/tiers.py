"""
REST API view for app tiers.
"""

from cornice.resource import resource, view

import tds.model

from . import utils
from .base import BaseView, init_view

@resource(collection_path="/tiers", path="/tiers/{name_or_id}")
@init_view(name='tier', model=tds.model.AppTarget)
class TierView(BaseView):
    """
    Tier view. This object maps to the /tiers and /tiers/{name_or_id} URLs.
    An object of this class is initalized to handle each request.
    The collection_* methods correspond to the /tiers URL while the
    others correspond to the /tiers/{name_or_id} URL.
    """

    # JSON types for params.
    types = {
        'id': 'number',
        'name': 'string',
        'distribution': 'string',
        'puppet_class': 'string',
        'ganglia_id': 'number',
        'ganglia_group_name': 'string',
        'status': 'string',
        'hipchats': 'string',
        'hosts': 'number',
    }

    # URL parameter routes to Python object fields.
    # Params not included are mapped to themselves.
    param_routes = {
        'name': 'app_type',
    }

    defaults = {}

    required_post_fields = ("name",)

    def validate_tier_post(self, _request):
        """
        Validate a POST request by preventing collisions over unique fields.
        """
        self._validate_id("POST")
        self._validate_name("POST")

    @view(validators=('validate_put_post', 'validate_post_required',
                      'validate_tier_post', 'validate_cookie'))
    def collection_post(self):
        """
        Handle a POST request after the parameters are marked valid JSON.
        """
        return self._handle_collection_post()
