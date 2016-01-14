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

    # Remove these choice fields when they are defined in TagOpsDB.
    arch_choices = ('i386', 'noarch', 'x86_64',)

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

    permissions = {
        'put': 'admin',
        'delete': 'admin',
        'collection_post': 'admin',
    }

    individual_allowed_methods = dict(
        GET=dict(description="Get host matching name or ID."),
        PUT=dict(description="Update host matching name or ID."),
    )

    collection_allowed_methods = dict(
        GET=dict(description="Get a list of hosts, optionally by limit and/"
                 "or start."),
        POST=dict(description="Add a new host."),
    )

    def validate_host_post(self):
        """
        Validate a POST request by preventing collisions over unique fields and
        validating that an app tier with the given tier_id exists.
        """
        self._validate_name("POST")
        self._validate_foreign_key('tier_id', 'app tier', tds.model.AppTarget)

    def validate_host_put(self):
        """
        Validate a PUT request by preventing collisions over unique fields and
        validating that an app tier with the given tier_id exists.
        """
        self._validate_name("PUT")
        self._validate_foreign_key('tier_id', 'app tier', tds.model.AppTarget)
