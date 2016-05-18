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

Feature: GET environment(s) from the REST API
    As a user
    I want information on environments
    So that I can use that information in further queries

    Background:
        Given I have a cookie with user permissions
        And there is an environment with name="dev"
        And there is an environment with name="staging"

    @rest
    Scenario Outline: get an environment that doesn't exist
        When I query GET "/environments/<select>"
        Then the response code is 404
        And the response contains errors:
            | location  | name          | description                               |
            | path      | name_or_id    | Environment with <desc> does not exist.   |

        Examples:
            | select    | desc          |
            | noexist   | name noexist  |
            | 500       | ID 500        |

    @rest
    Scenario: get all environments
        When I query GET "/environments"
        Then the response code is 200
        And the response is a list of 2 items
        And the response list contains objects:
            | name          | short_name    |
            | development   | dev           |
            | staging       | staging       |

    @rest
    Scenario Outline: get a single environment
        When I query GET "/environments/<select>"
        Then the response code is 200
        And the response is an object with id=1,name="development",short_name="dev"

        Examples:
            | select        |
            | 1             |
            | development   |
