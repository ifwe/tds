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

Feature: OPTIONS for login
    As a user
    I want to know what my options are for the login endpoint
    So that I can login without errors

    @rest
    Scenario: get options for the login endpoint
        When I query OPTIONS "/login"
        Then the response code is 200
        And the response header contains "Allows" set to "OPTIONS, POST"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "description"
        And the response body contains "Authenticate and get a session cookie using a JSON body with attributes 'username' and 'password'."
        And the response body contains "returns"
        And the response body contains "Session cookie attached at cookies->session."
        And the response body contains "permissions"
        And the response body contains "none"
