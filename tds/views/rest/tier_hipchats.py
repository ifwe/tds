# Copyright 2016 Ifwe Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
REST API view for Tier-Hipchat relationships.
"""

from cornice.resource import resource, view

import tds.model
import tagopsdb
from .base import BaseView, init_view
from . import obj_types, descriptions
from .urls import ALL_URLS
from .permissions import TIER_HIPCHAT_PERMISSIONS


@resource(collection_path=ALL_URLS['tier_hipchat_collection'],
          path=ALL_URLS['tier_hipchat'])
@init_view(name="tier-hipchat", model=tagopsdb.model.Hipchat, set_params=False)
class TierHipchatView(BaseView):
    """
    Tier-Hipchat relationship view.
    """

    types = {
        'id': 'integer',
        'name': 'string',
    }

    full_types = obj_types.HIPCHAT_TYPES

    param_descriptions = {
        'id': 'ID of the HipChat',
        'name': 'Name of the HipChat',
    }

    full_descriptions = descriptions.HIPCHAT_DESCRIPTIONS

    param_routes = {
        'name': 'room_name',
    }

    permissions = TIER_HIPCHAT_PERMISSIONS

    individual_allowed_methods = dict(
        GET=dict(description="Get a HipChat associated with the tier."),
        HEAD=dict(description="Do a GET query without a body returned."),
        DELETE=dict(
            description="Disassociate a HipChat from the tier.",
            returns="Disassociated HipChat",
        ),
    )

    collection_allowed_methods = dict(
        GET=dict(
            description="Get a list of HipChats associated with the tier, "
            "optionally by limit and/or start."
        ),
        HEAD=dict(description="Do a GET query without a body returned."),
        POST=dict(
            description="Associate a HipChat with the tier by name or "
                "ID (ID given precedence).",
            returns="Associated HipChat",
            ),
    )

    def validate_individual_tier_hipchat(self, request):
        """
        Validate the individual tier-HipChat association being referenced
        exists.
        """
        self.get_obj_by_name_or_id('tier', tds.model.AppTarget, 'app_type')
        if 'tier' in request.validated:
            self.get_obj_by_name_or_id(
                obj_type="HipChat",
                param_name='hipchat_name_or_id',
                model=self.model,
            )
            if 'HipChat' not in request.validated:
                return
            if request.validated['HipChat'] not in request.validated[
                'tier'
            ].hipchats:
                request.errors.add(
                    'path', 'hipchat_name_or_id',
                    "This tier-HipChat association does not exist."
                )
                request.errors.status = 404
            request.validated[self.name] = request.validated['HipChat']

    def validate_tier_hipchat_collection(self, request):
        """
        Validate the tier being referenced and HipChat being referenced exist.
        """
        self._validate_params(['select'])
        self._validate_json_params({'select': 'string'})
        self._validate_select_attributes(request)
        self.get_obj_by_name_or_id('tier', tds.model.AppTarget,
                                   'app_type')
        if 'tier' in request.validated:
            request.validated[self.plural] = request.validated[
                'tier'
            ].hipchats

    @view(validators=('validate_individual', 'validate_cookie'))
    def delete(self):
        """
        Perform a DELETE after all validation has passed.
        """
        self.request.validated['tier'].hipchats.remove(self.request.validated[
            'HipChat'
        ])
        self.session.commit()
        return self.make_response(
            self.to_json_obj(self.request.validated['HipChat'])
        )

    def validate_tier_hipchat_post(self, request):
        """
        Validate POST of a new tier-HipChat association.
        """
        self._validate_params(self.valid_attrs)
        self.get_obj_by_name_or_id('tier', tds.model.AppTarget, 'app_type')
        if 'tier' not in request.validated:
            return

        if 'id' in request.params:
            found = self.query(self.model).get(id=request.params['id'])
        elif 'name' in request.params:
            found = self.query(self.model).get(room_name=request.params['name'])
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
                    val=request.params.get('id', request.params.get('name')),
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
        """
        Handle collection POST after all validation has passed.
        """
        self.session.commit()
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
