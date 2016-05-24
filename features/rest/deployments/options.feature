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

Feature: OPTIONS for deployments
    As a user
    I want to know my options for the deployments endpoints
    So that I can avoid errors and be more effective in using the API

    @rest
    Scenario: get options for the collection endpoint
        When I query OPTIONS "/deployments"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, HEAD, OPTIONS, POST"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Get a list of deployments, optionally by limit and/or start."
        And the response body contains "Do a GET query without a body returned."
        And the response body contains "Add a new deployment."
        And the response body contains "Unique integer identifier"
        And the response body contains "returns"
        And the response body contains "Newly created deployment"

    @rest
    Scenario: get options for the individual endpoint
        When I query OPTIONS "/deployments/foo"
        Then the response code is 200
        And the response header contains "Allows" set to "DELETE, GET, HEAD, OPTIONS, PUT"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Get deployment matching ID."
        And the response body contains "Update deployment matching ID."
        And the response body contains "Delete deployment matching ID."
        And the response body contains "Do a GET query without a body returned."
        And the response body contains "cascade"
        And the response body contains "boolean"
        And the response body contains "Unique integer identifier"
        And the response body contains "Whether to delete all associated host and tier deployments"
        And the response body contains "force"
        And the response body contains "Whether to force queue the deployment despite lack of validation in the previous environment"
        And the response body contains "returns"
        And the response body contains "Deleted deployment"
