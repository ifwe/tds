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

Feature: GET deployment(s) from the REST API
    As a developer
    I want information on deployments
    So that I can be informed of the current state of the database

    Background:
        Given I have a cookie with user permissions

    @rest
    Scenario: no deployments
        When I query GET "/deployments"
        Then the response code is 200
        And the response is a list of 0 items

    @rest
    Scenario: get a deployment that doesn't exist
        When I query GET "/deployments/500"
        Then the response code is 404
        And the response contains errors:
            | location  | name  | description                               |
            | path      | id    | Deployment with ID 500 does not exist.    |

    @rest
    Scenario: get all deployments
        Given there are deployments:
            | id    | user  | status        | duration  |
            | 1     | foo   | pending       | 1         |
            | 2     | bar   | queued        | 0         |
            | 3     | baz   | inprogress    | 20        |
        When I query GET "/deployments"
        Then the response code is 200
        And the response is a list of 3 items
        And the response list contains an object with id=1,user="foo",status="pending",duration=1
        And the response list contains an object with id=2,user="bar",status="queued",duration=0
        And the response list contains an object with id=3,user="baz",status="inprogress",duration=20

    @rest
    Scenario: get all deployments with select query
        Given there are deployments:
            | id    | user  | status        | duration  |
            | 1     | foo   | pending       | 1         |
            | 2     | bar   | queued        | 0         |
            | 3     | baz   | inprogress    | 20        |
        When I query GET "/deployments?select=duration,declared"
        Then the response code is 200
        And the response is a list of 3 items
        And the response list contains an object with duration=1
        And the response list contains an object with duration=0
        And the response list contains an object with duration=20
        And the response list objects do not contain attributes id,user,status

    @rest
    Scenario: get a specific deployment
        Given there are deployments:
            | id    | user  | status        | duration  |
            | 1     | foo   | pending       | 1         |
            | 2     | bar   | queued        | 0         |
            | 3     | baz   | inprogress    | 20        |
        When I query GET "/deployments/2"
        Then the response code is 200
        And the response is an object with id=2,user="bar",status="queued",duration=0

    @rest
    Scenario: get a specific deployment with select query
        Given there are deployments:
            | id    | user  | status        | duration  |
            | 1     | foo   | pending       | 1         |
            | 2     | bar   | queued        | 0         |
            | 3     | baz   | inprogress    | 20        |
        When I query GET "/deployments/2?select=id,user"
        Then the response code is 200
        And the response is an object with id=2,user="bar"
        And the response object does not contain attributes status,duration

    @rest
    Scenario Outline: specify limit and/or last queries
        Given there are deployments:
            | id    | user  | status        |
            | 1     | foo   | pending       |
            | 2     | bar   | queued        |
            | 3     | baz   | inprogress    |
            | 4     | bar   | queued        |
            | 5     | baz   | inprogress    |
        When I query GET "/deployments?limit=<limit>&start=<start>"
        Then the response code is 200
        And the response is a list of <num> items
        And the response list contains id range <min> to <max>

        Examples:
            | limit | start | num   | min   | max   |
            |       |       | 5     | 1     | 5     |
            |       | 1     | 5     | 1     | 5     |
            | 10    |       | 5     | 1     | 5     |
            | 4     | 1     | 4     | 1     | 4     |
            |       |       | 5     | 1     | 5     |
            |       | 2     | 4     | 2     | 5     |
