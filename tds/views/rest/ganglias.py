"""
REST API view for Ganglia objects.
"""

from cornice.resource import resource

import tagopsdb
from .base import BaseView, init_view

@resource(collection_path="/ganglias", path="/ganglias/{name_or_id}")
@init_view(name="ganglia", model=tagopsdb.model.Ganglia)
class GangliaView(BaseView):
    """
    Ganglia view. This object maps to the /ganglias and /ganglias/{name_or_id}
    URLs.
    An object of this class is initialized to handle each request.
    The collection_* methods correspond to the /ganglias URL while the others
    correspond to the /ganglias/{name_or_id} URL.
    """

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

    individual_allowed_methods = dict(
        GET=dict(description="Get Ganglia matching name or ID."),
        PUT=dict(description="Update Ganglia matching name or ID."),
    )

    collection_allowed_methods = dict(
        GET=dict(description="Get a list of Ganglias, optionally by limit and/"
                 "or start."),
        POST=dict(description="Add a new Ganglia."),
    )
