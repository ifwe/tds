"""
REST API view for HipChat objects.
"""

from cornice.resource import resource

import tagopsdb
from .base import BaseView, init_view
from .urls import ALL_URLS
from .permissions import HIPCHAT_PERMISSIONS


@resource(collection_path=ALL_URLS['hipchat_collection'],
          path=ALL_URLS['hipchat'])
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

    permissions = HIPCHAT_PERMISSIONS

    individual_allowed_methods = dict(
        GET=dict(description="Get HipChat matching name or ID."),
        HEAD=dict(description="Do a GET query without a body returned."),
        PUT=dict(description="Update HipChat matching name or ID."),
    )

    collection_allowed_methods = dict(
        GET=dict(description="Get a list of HipChats, optionally by limit and/"
                 "or start."),
        HEAD=dict(description="Do a GET query without a body returned."),
        POST=dict(description="Add a new HipChat."),
    )
