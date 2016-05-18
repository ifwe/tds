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
Permission dictionaries for URL endpoints. These permissions are only used
wherever validate_cookie is passed as a validator.
In particular, the login and root URLs & the OPTIONS methods do not do any
cookie validation and are therefore not necessary here.
"""

APPLICATION_TIER_PERMISSIONS = dict(
    collection_get='user',
    collection_head='user',
    collection_post='user',
    get='user',
    head='user',
    delete='user',
)

APPLICATION_PERMISSIONS = dict(
    collection_get='user',
    collection_head='user',
    collection_post='admin',
    delete='admin',
    get='user',
    head='user',
    put='admin',
)

CURRENT_HOST_DEPLOYMENT_PERMISSIONS = dict(
    get='user',
    head='user',
)

CURRENT_TIER_DEPLOYMENT_PERMISSIONS = dict(
    get='user',
    head='user',
)

DEPLOYMENT_PERMISSIONS = dict(
    collection_get='user',
    collection_head='user',
    collection_post='user',
    delete='user',
    get='user',
    head='user',
    put='user',
)

ENVIRONMENT_PERMISSIONS = dict(
    collection_get='user',
    collection_head='user',
    collection_post='admin',
    delete='admin',
    get='user',
    head='user',
    put='admin',
)

GANGLIA_PERMISSIONS = dict(
    collection_get='user',
    collection_head='user',
    collection_post='admin',
    delete='admin',
    get='user',
    head='user',
    put='admin',
)

HIPCHAT_PERMISSIONS = dict(
    collection_get='user',
    collection_head='user',
    collection_post='admin',
    delete='admin',
    get='user',
    head='user',
    put='admin',
)

HOST_DEPLOYMENT_PERMISSIONS = dict(
    collection_get='user',
    collection_head='user',
    collection_post='user',
    delete='user',
    get='user',
    head='user',
    put='user',
)

HOST_PERMISSIONS = dict(
    collection_get='user',
    collection_head='user',
    collection_post='admin',
    delete='admin',
    get='user',
    head='user',
    put='admin',
)

PACKAGE_BY_ID_PERMISSIONS = dict(
    collection_get='user',
    collection_head='user',
    collection_post='user',
    delete='admin',
    get='user',
    head='user',
    put='user',
)

PACKAGE_PERMISSIONS = dict(
    collection_get='user',
    collection_head='user',
    collection_post='user',
    delete='admin',
    get='user',
    head='user',
    put='user',
)

PROJECT_PERMISSIONS = dict(
    collection_get='user',
    collection_head='user',
    collection_post='admin',
    delete='admin',
    get='user',
    head='user',
    put='admin',
)

ROOT_PERMISSIONS = dict(
    collection_get='user',
    collection_head='user',
    collection_post='user',
    delete='user',
    get='user',
    head='user',
    put='user',
)

SEARCH_PERMISSIONS = dict(
    get='user',
    head='user',
)

BYSTANDER_PERMISSIONS = dict(
    get='user',
    head='user',
)

TIER_DEPLOYMENT_PERMISSIONS = dict(
    collection_get='user',
    collection_head='user',
    collection_post='user',
    delete='user',
    get='user',
    head='user',
    put='user',
)

TIER_HIPCHAT_PERMISSIONS = dict(
    collection_get='user',
    collection_head='user',
    collection_post='user',
    delete='user',
    get='user',
    head='user',
    put='user',
)

TIER_PERMISSIONS = dict(
    collection_get='user',
    collection_head='user',
    collection_post='admin',
    delete='admin',
    get='user',
    head='user',
    put='admin',
)
