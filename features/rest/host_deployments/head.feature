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

Feature: HEAD host deployment(s) from the REST API
    As a developer
    I want to test my GET query
    So that I can be sure my query is not malformed

    Background:
        Given I have a cookie with user permissions
        And there is an application with pkg_name="app1"
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | pending   |
        And there is an environment with name="dev"
        And there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |

    @rest
    Scenario: no host deployments
        When I query HEAD "/host_deployments"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario: get host deployment that doesn't exist
        When I query HEAD "/host_deployments/500"
        Then the response code is 404
        And the response body is empty

    @rest
    Scenario: get all host deployments
        Given there are host deployments:
            | id    | deployment_id | host_id   | status        | user  | package_id    | duration  |
            | 1     | 1             | 1         | pending       | foo   | 1             | 2         |
            | 2     | 1             | 2         | inprogress    | foo   | 1             | 20        |
        When I query HEAD "/host_deployments"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario: get a specific host deployment
        Given there are host deployments:
            | id    | deployment_id | host_id   | status        | user  | package_id    | duration  |
            | 1     | 1             | 1         | pending       | foo   | 1             | 2         |
            | 2     | 1             | 2         | inprogress    | foo   | 1             | 20        |
        When I query HEAD "/host_deployments/1"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario Outline: specify limit and/or last queries
        Given there are hosts:
            | name  | env   |
            | host3 | dev   |
            | host4 | dev   |
            | host5 | dev   |
        And there are host deployments:
            | id    | deployment_id | host_id   | status        | user  | package_id    |
            | 1     | 1             | 1         | pending       | foo   | 1             |
            | 2     | 1             | 2         | inprogress    | foo   | 1             |
            | 3     | 1             | 3         | pending       | foo   | 1             |
            | 4     | 1             | 4         | inprogress    | foo   | 1             |
            | 5     | 1             | 5         | pending       | foo   | 1             |
        When I query HEAD "/host_deployments?limit=<limit>&start=<start>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | limit | start |
            |       |       |
            |       | 1     |
            | 10    |       |
            | 4     | 1     |
            |       |       |
            |       | 2     |
