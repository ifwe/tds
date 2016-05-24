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

Feature: OPTIONS for tier-HipChats
    As a developer
    I want to know my options for the tier-HipChats endpoints
    So that I can avoid errors and be more effective in using the API

    @rest
    Scenario: get options for the collection endpoint
        When I query OPTIONS "/tiers/foo/hipchats"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, HEAD, OPTIONS, POST"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Get a list of HipChats associated with the tier, optionally by limit and/or start."
        And the response body contains "Associate a HipChat with the tier by name or ID (ID given precedence)."
        And the response body contains "Do a GET query without a body returned."
        And the response body contains "name"
        And the response body contains "id"
        And the response body contains "returns"
        And the response body contains "Associated HipChat"

    @rest
    Scenario: get options for the individual endpoint
        When I query OPTIONS "/tiers/foo/hipchats/bar"
        Then the response code is 200
        And the response header contains "Allows" set to "DELETE, GET, HEAD, OPTIONS"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Get a HipChat associated with the tier."
        And the response body contains "Disassociate a HipChat from the tier."
        And the response body contains "Do a GET query without a body returned."
        And the response body contains "name"
        And the response body contains "id"
        And the response body contains "returns"
        And the response body contains "Disassociated HipChat"
