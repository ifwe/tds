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
REST API view for hosts.
"""

from cornice.resource import resource, view

import tds

from . import utils
from .base import BaseView, init_view
from .urls import ALL_URLS
from .permissions import HOST_PERMISSIONS


@resource(collection_path=ALL_URLS['host_collection'], path=ALL_URLS['host'])
@init_view(name='host', model=tds.model.HostTarget)
class HostView(BaseView):
    """
    Application view. This object maps to the /hosts and
    /hosts/{name_or_id} URLs.
    An object of this class is initalized to handle each request.
    The collection_* methods correspond to the /hosts URL while the
    others correspond to the /hosts/{name_or_id} URL.
    """

    # Remove these choice fields when they are defined in TagOpsDB.
    arch_choices = ('i386', 'noarch', 'x86_64',)

    # URL parameter routes to Python object fields.
    # Params not included are mapped to themselves.
    param_routes = {
        'name': 'hostname',
        'cage': 'cage_location',
        'cab': 'cab_location',
        'elevation': 'elevation',
        'tier_id': 'app_id',
    }

    defaults = {
        'state': 'operational',
    }

    required_post_fields = ("name", "tier_id")

    permissions = HOST_PERMISSIONS

    individual_allowed_methods = dict(
        GET=dict(description="Get host matching name or ID."),
        HEAD=dict(description="Do a GET query without a body returned."),
        PUT=dict(description="Update host matching name or ID."),
    )

    collection_allowed_methods = dict(
        GET=dict(description="Get a list of hosts, optionally by limit and/"
                 "or start."),
        HEAD=dict(description="Do a GET query without a body returned."),
        POST=dict(description="Add a new host."),
    )

    def validate_host_post(self):
        """
        Validate a POST request by preventing collisions over unique fields and
        validating that an app tier with the given tier_id exists.
        """
        self._validate_name("POST")
        self._validate_foreign_key('tier_id', 'app tier', tds.model.AppTarget)

    def validate_host_put(self):
        """
        Validate a PUT request by preventing collisions over unique fields and
        validating that an app tier with the given tier_id exists.
        """
        self._validate_name("PUT")
        self._validate_foreign_key('tier_id', 'app tier', tds.model.AppTarget)
