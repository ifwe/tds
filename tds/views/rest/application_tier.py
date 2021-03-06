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
REST API view for Application-Tier-Project relationships.
"""


from cornice.resource import resource, view

import tds.model
import tagopsdb
from .base import BaseView, init_view
from . import obj_types, descriptions
from .urls import ALL_URLS
from .permissions import APPLICATION_TIER_PERMISSIONS


@resource(collection_path=ALL_URLS['application_tier_collection'],
          path=ALL_URLS['application_tier'])
@init_view(name="application-tier", model=tagopsdb.model.ProjectPackage,
           set_params=False)
class ApplicationTierView(BaseView):
    """
    Tier-application-project relationship. Project should be passed as a param
    to filter application-tier relationships.
    """

    individual_allowed_methods = dict(
        GET=dict(description="Get project-application-tier association."),
        HEAD=dict(description="Do a GET query without a body returned."),
        DELETE=dict(
            description="Delete project-application-tier association.",
            returns="Deleted project-application-tier association.",
        ),
    )

    collection_allowed_methods = dict(
        GET=dict(
            description="Get all project-application-tier associations."
        ),
        HEAD=dict(description="Do a GET query without a body returned."),
        POST=dict(
            description="Create new association for project-application "
                "of tier with given ID or name (ID given precedence).",
            returns="Newly created project-application-tier association",
        ),
    )

    types = {
        'id': 'integer',
        'name': 'string',
    }

    full_types = obj_types.APPLICATION_TIER_TYPES

    param_descriptions = {
        'id': 'Unique integer identifier for the tier',
        'name': 'Unique string identifier for the tier',
    }

    full_descriptions = descriptions.APPLICATION_TIER_DESCRIPTIONS

    param_routes = {
        'application_id': 'pkg_def_id',
        'tier_id': 'app_id',
    }

    permissions = APPLICATION_TIER_PERMISSIONS

    def validate_individual_application_tier(self, request):
        """
        Validate that the tier-application-project relationship being
        referenced exists. If one is found, assing it to
        request.validated_params[self.name].
        """
        self.get_obj_by_name_or_id('project', tds.model.Project)
        self.get_obj_by_name_or_id('application', tds.model.Application,
                                   'pkg_name',
                                   param_name='application_name_or_id')
        self.get_obj_by_name_or_id('tier', tds.model.AppTarget, 'app_type',
                                   param_name='tier_name_or_id')
        if not all(
            x in request.validated for x in ('project', 'application', 'tier')
        ):
            return
        found = self.query(self.model).get(
            project_id=request.validated['project'].id,
            pkg_def_id=request.validated['application'].id,
            app_id=request.validated['tier'].id,
        )
        if not found:
            request.errors.add(
                'path', 'tier_name_or_id',
                'Association of tier {t_name} with the application {a_name}'
                ' for the project {p_name} does not exist.'.format(
                    t_name=request.validated['tier'].name,
                    a_name=request.validated['application'].name,
                    p_name=request.validated['project'].name,
                )
            )
            request.errors.status = 404
        request.validated[self.name] = found

    def validate_application_tier_collection(self, request):
        """
        Validate application and project being referenced exist and return
        all associated tiers for that application-project pair.
        """
        self._validate_params(['limit', 'select'])
        self._validate_json_params({'limit': 'integer', 'select': 'string'})
        self._validate_select_attributes(request)
        self.get_obj_by_name_or_id('project', tds.model.Project)
        self.get_obj_by_name_or_id('application', tds.model.Application,
                                   'pkg_name',
                                   param_name='application_name_or_id')
        if all(x in request.validated for x in ('project', 'application')):
            query = self.query(self.model).filter(
                self.model.project_id == request.validated['project'].id,
                self.model.pkg_def_id == request.validated['application'].id,
            )
            if 'limit' in request.validated_params:
                query = query.limit(self.request.validated_params['limit'])
            request.validated[self.plural] = query.all()

    def validate_application_tier_post(self, request):
        """
        Validate POST of a new tier-application-project relationship.
        """
        self._validate_params(self.valid_attrs)
        self.get_obj_by_name_or_id('project', tds.model.Project)
        self.get_obj_by_name_or_id('application', tds.model.Application,
                                   'pkg_name',
                                   param_name='application_name_or_id')
        if not all(x in request.validated for x in ('project', 'application')):
            return
        if 'id' in request.validated_params:
            found = self.query(tds.model.AppTarget).get(
                id=request.validated_params['id']
            )
        elif 'name' in request.validated_params:
            found = self.query(tds.model.AppTarget).get(
                name=request.validated_params['name']
            )
        else:
            request.errors.add(
                'query', '',
                "Either name or ID for the tier is required."
            )
            request.errors.status = 400
            return

        if not found:
            request.errors.add(
                'query', 'id' if 'id' in request.validated_params else 'name',
                "Tier with {param} {val} does not exist.".format(
                    param="ID" if 'id' in request.validated_params else 'name',
                    val=request.validated_params['id'] if 'id' in
                        request.validated_params else
                        request.validated_params['name'],
                )
            )
            request.errors.status = 400
            return

        already_exists = self.query(tagopsdb.model.ProjectPackage).get(
            project_id=request.validated['project'].id,
            pkg_def_id=request.validated['application'].id,
            app_id=found.id,
        )
        if already_exists is not None:
            self.response_code = "200 OK"
            request.validated[self.name] = already_exists
            return
        request.validated[self.name] = tagopsdb.model.ProjectPackage(
            project_id=request.validated['project'].id,
            pkg_def_id=request.validated['application'].id,
            app_id=found.id,
        )
        self.response_code = "201 Created"

    @view(validators=('validate_application_tier_post', 'validate_cookie'))
    def collection_post(self):
        """
        Handle collection POST after all validation has passed.
        """
        self.session.add(self.request.validated[self.name])
        self.session.commit()
        return self.make_response(
            self.to_json_obj(self.request.validated[self.name]),
            self.response_code,
        )

    @view(validators=('validate_individual', 'validate_cookie'))
    def delete(self):
        """
        Handle DELETE after all validation has passed.
        """
        self.session.delete(self.request.validated[self.name])
        self.session.commit()
        return self.make_response(
            self.to_json_obj(self.request.validated[self.name])
        )

    @view(validators=('method_not_allowed'))
    def put(self):
        """
        Method not allowed.
        """
        pass
