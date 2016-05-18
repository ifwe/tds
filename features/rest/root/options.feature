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

Feature: REST API root OPTIONS
    As a developer
    I want to know my param options for the root URL endpoint
    So that I can use the root URL endpoing more effectively

    @rest
    Scenario: get options for root URL
        When I query OPTIONS on the root url
        Then the response code is 200
        And the response header contains "Allows" set to "GET, HEAD, OPTIONS"
        And the response body contains "Get all supported URLS."
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Do a GET query without a body returned."
        And the response body contains "description"
        And the response body contains "GET"
        And the response body contains "OPTIONS"
