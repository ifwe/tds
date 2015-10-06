"""
REST API view for HipChat objects.
"""

from cornice.resource import resource, view

import tagopsdb
from .base import BaseView, init_view

@resource(collection_path="/hipchats", path="/hipchats/{name_or_id}")
@init_view(name="hipchat", model=tagopsdb.model.Hipchat)
class HipchatView(BaseView):
    """
    HipChat view. This object maps to the /hipchats and /hipchats/{name_or_id}
    URLs.
    An object of this class is initialized to handle each request.
    The collection_* methods correspond to the /hipchats URL while the others
    correspond to the /hipchats/{name_or_id} URL.
    """

    # URL parameter routes to Python object fields.
    # Params not included are mapped to themselves.
    param_routes = {
        'name': 'room_name',
    }

    defaults = {}

    required_post_fields = ("name",)

    permissions = {
        'put': 'admin',
        'delete': 'admin',
        'collection_post': 'admin',
    }
