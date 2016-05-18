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

Feature: REST API performance OPTIONS
    As a developer
    I want to know my param options for the performance endpoint
    So that I can avoid errors in my queries

    @rest
    Scenario: get options for the performance endpoint
        When I query OPTIONS "/performance/packages"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, HEAD, OPTIONS"
        And the response body contains "Get metrics on packages, tier deployments, host deployments, or deployments by month for all months."
        And the response body contains "Do a GET query without a body returned."
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
