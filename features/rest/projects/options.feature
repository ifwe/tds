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

Feature: OPTIONS for projects
    As a user
    I want to know my options for the projects endpoints
    So that I can avoid errors and be more effective in using the API

    @rest
    Scenario: get options for the collection endpoint
        When I query OPTIONS "/projects"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, HEAD, OPTIONS, POST"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Get a list of projects, optionally by limit and/or start."
        And the response body contains "Add a new project."
        And the response body contains "Do a GET query without a body returned."
        And the response body contains "permissions"
        And the response body contains "user"
        And the response body contains "admin"
        And the response body contains "id"
        And the response body contains "Unique integer identifier"
        And the response body contains "name"
        And the response body contains "Unique string identifier"
        And the response body contains "required"

    @rest
    Scenario: get options for the individual endpoint
        When I query OPTIONS "/projects/foo"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, HEAD, OPTIONS, PUT"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Get project matching name or ID."
        And the response body contains "Update project matching name or ID."
        And the response body contains "Do a GET query without a body returned."
        And the response body contains "permissions"
        And the response body contains "user"
        And the response body contains "admin"
        And the response body contains "Unique integer identifier"
        And the response body contains "id"
        And the response body contains "name"
        And the response body contains "Unique string identifier"
