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
