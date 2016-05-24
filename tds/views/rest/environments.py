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
REST API view for environment objects.
"""

from cornice.resource import resource, view

import tagopsdb
from .base import BaseView, init_view
from .urls import ALL_URLS
from .permissions import ENVIRONMENT_PERMISSIONS


@resource(collection_path=ALL_URLS['environment_collection'],
          path=ALL_URLS['environment'])
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

    permissions = ENVIRONMENT_PERMISSIONS

    unique = ('short_name', 'domain', 'prefix')

    individual_allowed_methods = dict(
        GET=dict(description="Get environment matching name or ID."),
        HEAD=dict(description="Do a GET query without a body returned."),
        PUT=dict(description="Update environment matching name or ID."),
    )

    collection_allowed_methods = dict(
        GET=dict(description="Get a list of environments, optionally by limit "
                 "and/or start."),
        HEAD=dict(description="Do a GET query without a body returned."),
        POST=dict(description="Add a new environment."),
    )
