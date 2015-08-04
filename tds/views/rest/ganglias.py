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

    permissions = {
        'put': 'admin',
        'delete': 'admin',
        'collection_post': 'admin',
    }
