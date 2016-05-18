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
REST API view for applications.
"""

from cornice.resource import resource, view

import tagopsdb

from .base import BaseView, init_view
from .urls import ALL_URLS
from .permissions import APPLICATION_PERMISSIONS


@resource(collection_path=ALL_URLS['application_collection'],
          path=ALL_URLS['application'])
@init_view(name='application')
class ApplicationView(BaseView):
    """
    Application view. This object maps to the /applications and
    /applications/{name_or_id} URLs.
    An object of this class is initalized to handle each request.
    The collection_* methods correspond to the /applications URL while the
    others correspond to the /applications/{name_or_id} URL.
    """

    # URL parameter routes to Python object fields.
    # Params not included are mapped to themselves.
    param_routes = {
        'name': 'pkg_name',
        'job': 'path',
    }

    individual_allowed_methods = dict(
        GET=dict(description="Get application matching name or ID."),
        HEAD=dict(description="Do a GET query without a body returned."),
        PUT=dict(description="Update application matching name or ID."),
    )

    collection_allowed_methods = dict(
        GET=dict(description="Get a list of applications, optionally by limit "
                 "and/or start."),
        HEAD=dict(description="Do a GET query without a body returned."),
        POST=dict(description="Add a new application."),
    )

    defaults = {
        'arch': 'noarch',
        'build_type': 'jenkins',
        'build_host': 'build_host',
        'deploy_type': 'rpm',
        'validation_type': 'matching',
    }

    required_post_fields = ("name", "job")

    permissions = APPLICATION_PERMISSIONS
