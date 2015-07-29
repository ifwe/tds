"""
REST API view for hosts.
"""

from cornice.resource import resource, view

import tds

from . import utils
from .base import BaseView, init_view

@resource(collection_path="/hosts", path="/hosts/{name_or_id}")
@init_view(name='host', model=tds.model.HostTarget)
class HostView(BaseView):
    """
    Application view. This object maps to the /hosts and
    /hosts/{name_or_id} URLs.
    An object of this class is initalized to handle each request.
    The collection_* methods correspond to the /hosts URL while the
    others correspond to the /hosts/{name_or_id} URL.
    """

    # JSON types for params.
    types = {
        'id': 'integer',
        'name': 'string',
        'tier_id': 'integer',
        'cage': 'integer',
        'cab': 'string',
        'rack': 'integer',
        'kernel_version': 'string',
        'console_port': 'string',
        'power_port': 'string',
        'power_circuit': 'string',
        'state': 'string',
        'arch': 'string',
        'distribution': 'string',
        'timezone': 'string',
        'environment_id': 'integer',
    }

    # URL parameter routes to Python object fields.
    # Params not included are mapped to themselves.
    param_routes = {
        'name': 'hostname',
        'cage': 'cage_location',
        'cab': 'cab_location',
        'rack': 'rack_location',
        'tier_id': 'app_id',
    }

    defaults = {
        'state': 'operational',
    }

    required_post_fields = ("name", "tier_id")

    def validate_host_post(self, _request):
        """
        Validate a POST request by preventing collisions over unique fields.
        """
        self._validate_id("POST")
        self._validate_name("POST")
        if 'tier_id' in self.request.validated_params:
            found_app = tds.model.AppTarget.get(
                id=self.request.validated_params['tier_id']
            )
            if found_app is None:
                self.request.errors.add(
                    'query', 'tier_id',
                    "No app tier with this ID exists."
                )
                self.request.errors.status = 400

    @view(validators=('validate_put_post', 'validate_post_required',
                      'validate_host_post', 'validate_cookie'))
    def collection_post(self):
        """
        Handle a POST request after the parameters are marked valid JSON.
        """
        return self._handle_collection_post()
