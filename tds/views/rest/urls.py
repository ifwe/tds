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
All URLs supported.
"""

ALL_URLS = dict(
    application_tier_collection='/projects/{name_or_id}/applications/'
        '{application_name_or_id}/tiers',
    application_tier='/projects/{name_or_id}/applications/'
        '{application_name_or_id}/tiers/{tier_name_or_id}',
    application_collection='/applications',
    application='/applications/{name_or_id}',
    bystander='/bystander',
    current_host_deployment='/applications/{name_or_id}/hosts/'
        '{host_name_or_id}',
    current_tier_deployment='/applications/{name_or_id}/tiers/'
        '{tier_name_or_id}/environments/{environment_name_or_id}',
    deployment_collection='/deployments',
    deployment='/deployments/{id}',
    environment_collection='/environments',
    environment='/environments/{name_or_id}',
    ganglia_collection='/ganglias',
    ganglia='/ganglias/{name_or_id}',
    hipchat_collection='/hipchats',
    hipchat='/hipchats/{name_or_id}',
    host_deployment_collection='/host_deployments',
    host_deployment='/host_deployments/{id}',
    host_collection='/hosts',
    host='/hosts/{name_or_id}',
    login='/login',
    package_by_id_collection='/packages',
    package_by_id='/packages/{id}',
    package_collection='/applications/{name_or_id}/packages',
    package='/applications/{name_or_id}/packages/{version}/{revision}',
    performance='/performance/{obj_type}',
    project_collection='/projects',
    project='/projects/{name_or_id}',
    search='/search/{obj_type}',
    tier_deployment_collection='/tier_deployments',
    tier_deployment='/tier_deployments/{id}',
    tier_hipchat_collection='/tiers/{name_or_id}/hipchats',
    tier_hipchat='/tiers/{name_or_id}/hipchats/{hipchat_name_or_id}',
    tier_collection='/tiers',
    tier='/tiers/{name_or_id}',
)
