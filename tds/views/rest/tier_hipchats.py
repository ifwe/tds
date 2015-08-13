"""
REST API view for Tier-Hipchat relationships.
"""

from cornice.resource import resource, view

import tds.model
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

    @view(validators=('validate_individual', 'validate_cookie'))
    def delete(self):
        self.request.validated['tier'].hipchats.remove(self.request.validated[
            'HipChat'
        ])
        tagopsdb.Session.commit()
        return self.make_response(
            self.to_json_obj(self.request.validated['HipChat'])
        )

    def validate_tier_hipchat_post(self, request):
        self._validate_params(self.valid_attrs)
        self.get_obj_by_name_or_id('tier', tds.model.AppTarget, 'app_type')
        if 'tier' not in request.validated:
            return

        if 'id' in request.params:
            found = self.model.get(id=request.params['id'])
        elif 'name' in request.params:
            found = self.model.get(room_name=request.params['name'])
        else:
            request.errors.add(
                'query', '',
                "Either name or ID for the HipChat is required."
            )
            request.errors.status = 400
            return

        if not found:
            request.errors.add(
                'query', 'id' if 'id' in request.params else 'name',
                "Hipchat with {param} {val} does not exist.".format(
                    param='ID' if 'id' in request.params else 'name',
                    val=request.params['id'] if 'id' in request.params else
                        request.params['name'],
                )
            )
            request.errors.status = 404
            return
        request.validated[self.name] = found

        if found in request.validated['tier'].hipchats:
            self.response_code = "200 OK"
        else:
            request.validated['tier'].hipchats.append(found)
            self.response_code = "201 Created"

    @view(validators=('validate_tier_hipchat_post', 'validate_cookie'))
    def collection_post(self):
        tagopsdb.Session.commit()
        return self.make_response(
            self.to_json_obj(self.request.validated[self.name]),
            self.response_code,
        )

    @view(validators=('method_not_allowed'))
    def put(self):
        """
        Method not allowed.
        """
        return self.make_response({})
