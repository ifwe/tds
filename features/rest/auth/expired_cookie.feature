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

Feature: Expired cookie detection
    As an API developer
    I want to prevent users from gaining access with expired cookies
    So that the API can be secure

    @rest
    Scenario: attempt to use an expired cookie
        Given I have a cookie with user permissions
        And I change cookie life to 1
        And I wait 3 seconds
        When I query GET "/projects"
        Then the response code is 419
        And the response contains errors:
            | location  | name      | description                                               |
            | header    | cookie    | Cookie has expired or is invalid. Please reauthenticate.  |

    @rest
    Scenario: use an eternal cookie to get access after cookie life
        Given "testuser" is an eternal user in the REST API
        And I have a cookie with user permissions and eternal=True
        And I change cookie life to 1
        And I wait 3 seconds
        When I query GET "/projects"
        Then the response code is 200
