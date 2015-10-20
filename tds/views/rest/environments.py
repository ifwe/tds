"""
REST API view for environment objects.
"""

from cornice.resource import resource, view

import tagopsdb
from .base import BaseView, init_view

@resource(collection_path="/environments", path="/environments/{name_or_id}")
@init_view(name="environment", model=tagopsdb.model.Environment)
class EnvironmentView(BaseView):

    param_routes = {
        'name': 'environment',
        'short_name': 'env',
    }

    defaults = {
        'prefix': '',
    }

    required_post_fields = ("name", "short_name", "domain", "zone_id")

    permissions = {
        'put': 'admin',
        'delete': 'admin',
        'collection_post': 'admin',
    }

    unique = ('short_name', 'domain', 'prefix')

    individual_allowed_methods = dict(
        GET=dict(description="Get environment matching name or ID."),
        PUT=dict(description="Update environment matching name or ID."),
    )

    collection_allowed_methods = dict(
        GET=dict(description="Get a list of environments, optionally by limit "
                 "and/or start."),
        POST=dict(description="Add a new environment."),
    )
