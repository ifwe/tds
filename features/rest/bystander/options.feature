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

Feature: REST API bystander OPTIONS
    As a developer
    I want to know my param options for the bystander endpoint
    So that I can avoid errors in my queries

    @rest
    Scenario: get options for the bystander endpoint
        When I query OPTIONS "/bystander"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, HEAD, OPTIONS"
        And the response body contains "Get latest deployed version of all applications on all associated tiers in each environment, filtered by limit and/or start. NOTE: This method guarantees only that up to limit number of applications will be covered; applications should not expect exactly limit entries."
        And the response body contains "Do a GET query without a body returned."
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "limit"
        And the response body contains "Number of tiers to cover"
        And the response body contains "start"
        And the response body contains "ID of the first tier in this page"
