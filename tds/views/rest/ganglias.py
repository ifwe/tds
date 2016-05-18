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
REST API view for Ganglia objects.
"""

from cornice.resource import resource

import tagopsdb
from .base import BaseView, init_view
from .urls import ALL_URLS
from .permissions import GANGLIA_PERMISSIONS


@resource(collection_path=ALL_URLS['ganglia_collection'],
          path=ALL_URLS['ganglia'])
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

    permissions = GANGLIA_PERMISSIONS

    individual_allowed_methods = dict(
        GET=dict(description="Get Ganglia matching name or ID."),
        HEAD=dict(description="Do a GET query without a body returned."),
        PUT=dict(description="Update Ganglia matching name or ID."),
    )

    collection_allowed_methods = dict(
        GET=dict(description="Get a list of Ganglias, optionally by limit and/"
                 "or start."),
        HEAD=dict(description="Do a GET query without a body returned."),
        POST=dict(description="Add a new Ganglia."),
    )
