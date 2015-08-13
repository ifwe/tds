"""
REST API view for Tier-Hipchat relationships.
"""

from cornice.resource import resource, view

import tagopsdb
from .base import BaseView, init_view

@resource(collection_path="/tiers/{name_or_id}/hipchats",
          path="/tiers/{name_or_id}/hipchats/{hipchat_name_or_id}")
@init_view(name="tier-hipchat", model=tagopsdb.model.Hipchat)
class TierHipchatView(BaseView):
    """
    Tier-Hipchat relationship view.
    """

    types = {
        'id': 'integer',
        'name': 'string',
    }

    param_routes = {
        'name': 'room_name',
    }

    permissions = {}

    @view(validators=('validate_individual', 'validate_cookie'))
    def delete(self):
        pass

    @view(validators=('method_not_allowed'))
    def put(self):
        """
        Method not allowed.
        """
        return self.make_response({})
