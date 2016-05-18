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
REST API view for projects.
"""

from cornice.resource import resource

from .base import BaseView, init_view
from .urls import ALL_URLS
from .permissions import PROJECT_PERMISSIONS


@resource(collection_path=ALL_URLS['project_collection'],
          path=ALL_URLS['project'])
@init_view(name='project')
class ProjectView(BaseView):
    """
    Project view. This object maps to the /projects and /projects/{name_or_id}
    URLs.
    An object of this class is initalized to handle each request.
    The collection_* methods correspond to the /projects URL while the others
    correspond to the /projects/{name_or_id} URL.
    """

    required_post_fields = ('name',)

    permissions = PROJECT_PERMISSIONS

    individual_allowed_methods = dict(
        GET=dict(description="Get project matching name or ID."),
        HEAD=dict(description="Do a GET query without a body returned."),
        PUT=dict(description="Update project matching name or ID."),
    )

    collection_allowed_methods = dict(
        GET=dict(description="Get a list of projects, optionally by limit and/"
                 "or start."),
        HEAD=dict(description="Do a GET query without a body returned."),
        POST=dict(description="Add a new project."),
    )
