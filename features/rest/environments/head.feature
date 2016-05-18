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

Feature: HEAD environment(s) from the REST API
    As a user
    I want to test my GET query
    So that I can be sure my query is not malformed

    Background:
        Given I have a cookie with user permissions
        And there is an environment with name="dev"
        And there is an environment with name="staging"

    @rest
    Scenario Outline: get an environment that doesn't exist
        When I query HEAD "/environments/<select>"
        Then the response code is 404
        And the response body is empty

        Examples:
            | select    |
            | noexist   |
            | 500       |

    @rest
    Scenario: get all environments
        When I query HEAD "/environments"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario Outline: get a single environment
        When I query HEAD "/environments/<select>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | select        |
            | 1             |
            | development   |
