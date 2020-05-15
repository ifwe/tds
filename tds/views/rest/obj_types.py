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
JSON types for different resources.
"""

APPLICATION_TYPES = {
    'id': 'integer',
    'name': 'string',
    'job': 'string',
    'repository': 'string',
    'build_host': 'string',
    'build_type': 'choice',
    'deploy_type': 'string',
    'arch': 'choice',
    'validation_type': 'string',
    'env_specific': 'boolean',
    'created': 'timestamp',
}

APPLICATION_TIER_TYPES = {
    'project_id': 'integer',
    'application_id': 'integer',
    'tier_id': 'integer',
}

DEPLOYMENT_TYPES = {
    'id': 'integer',
    'user': 'string',
    'status': 'choice',
    'delay': 'integer',
    'duration': 'number',
    'declared': 'timestamp',
}

ENVIRONMENT_TYPES = {
    'id': 'integer',
    'name': 'string',
    'short_name': 'string',
    'domain': 'string',
    'prefix': 'string',
    'zone_id': 'integer',
}

GANGLIA_TYPES = {
    'id': 'integer',
    'name': 'string',
    'port': 'integer',
}

HIPCHAT_TYPES = {
    'id': 'integer',
    'name': 'string',
}

HOST_TYPES = {
    'id': 'integer',
    'name': 'string',
    'tier_id': 'integer',
    'cage': 'integer',
    'cab': 'string',
    'rack': 'integer',
    'elevation': 'integer',
    'state': 'choice',
    'distribution': 'string',
    'environment_id': 'integer',
    'spec_id': 'integer',
    'dc_id': 'integer',
}

HOST_DEPLOYMENT_TYPES = {
    'id': 'integer',
    'deployment_id': 'integer',
    'host_id': 'integer',
    'package_id': 'integer',
    'status': 'choice',
    'user': 'string',
    'duration': 'number',
    'realized': 'timestamp',
    'deploy_result': 'string',
}

PACKAGE_TYPES = {
    'id': 'integer',
    'version': 'integer',
    'revision': 'integer',
    'status': 'choice',
    'builder': 'choice',
    'job': 'string',
    'application_id': 'integer',
    'created': 'timestamp',
    'user': 'string',
    'name': 'string',
    'project_type': 'choice',
    'commit_hash': 'string',
}

PROJECT_TYPES = {
    'id': 'number',
    'name': 'string',
}

TIER_TYPES = {
    'id': 'integer',
    'name': 'string',
    'distribution': 'string',
    'puppet_class': 'string',
    'ganglia_id': 'integer',
    'ganglia_name': 'string',
    'status': 'choice',
    'description': 'string',
    'host_base': 'string',
}

TIER_DEPLOYMENT_TYPES = {
    'id': 'integer',
    'deployment_id': 'integer',
    'tier_id': 'integer',
    'package_id': 'integer',
    'status': 'choice',
    'environment_id': 'integer',
    'user': 'string',
    'skewed': 'boolean',
    'duration': 'number',
    'realized': 'timestamp',
}
