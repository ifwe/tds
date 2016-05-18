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

Feature: OPTIONS for most recent tier deployment
    As a user
    I want to know my options for the most recent tier deployment endpoint
    So that I can avoid errors and be more effective in using the API

    @rest
    Scenario: get options for the endpoint
        When I query OPTIONS "/applications/foo/tiers/bar/environments/biz"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, HEAD, OPTIONS"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Get the most recent completed tier deployment for an application, tier, and environment."
        And the response body contains "Do a GET query without a body returned."
        And the response body contains "id"
        And the response body contains "deployment_id"
        And the response body contains "package_id"
        And the response body contains "tier_id"
        And the response body contains "Unique integer identifier"
