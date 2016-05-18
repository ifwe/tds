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

Feature: OPTIONS for tier deployments
    As a user
    I want to know my options for the tier deployments endpoints
    So that I can avoid errors and be more effective in using the API

    @rest
    Scenario: get options for the collection endpoint
        When I query OPTIONS "/tier_deployments"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, HEAD, OPTIONS, POST"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Get a list of tier deployments, optionally by limit and/or start."
        And the response body contains "Add a new tier deployment."
        And the response body contains "Do a GET query without a body returned."
        And the response body contains "permissions"
        And the response body contains "user"
        And the response body contains "id"
        And the response body contains "tier_id"
        And the response body contains "deployment_id"
        And the response body contains "environment_id"
        And the response body contains "Unique integer identifier"
        And the response body contains "unique_together"
        And the response body contains "required"
        And the response body contains "returns"

    @rest
    Scenario: get options for the individual endpoint
        When I query OPTIONS "/tier_deployments/foo"
        Then the response code is 200
        And the response header contains "Allows" set to "DELETE, GET, HEAD, OPTIONS, PUT"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Get tier deployment matching ID."
        And the response body contains "Update tier deployment matching ID."
        And the response body contains "Delete tier deployment matching ID."
        And the response body contains "Do a GET query without a body returned."
        And the response body contains "permissions"
        And the response body contains "user"
        And the response body contains "Unique integer identifier"
        And the response body contains "unique_together"
        And the response body contains "id"
        And the response body contains "tier_id"
        And the response body contains "deployment_id"
        And the response body contains "environment_id"
        And the response body contains "returns"
