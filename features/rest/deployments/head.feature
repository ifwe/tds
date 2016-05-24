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

Feature: HEAD deployment(s) from the REST API
    As a developer
    I want to test my GET query
    So that I can be sure my query is not malformed

    Background:
        Given I have a cookie with user permissions

    @rest
    Scenario: no deployments
        When I query HEAD "/deployments"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario: get a deployment that doesn't exist
        When I query HEAD "/deployments/500"
        Then the response code is 404
        And the response body is empty

    @rest
    Scenario: get all deployments
        Given there are deployments:
            | id    | user  | status        | duration  |
            | 1     | foo   | pending       | 1         |
            | 2     | bar   | queued        | 0         |
            | 3     | baz   | inprogress    | 20        |
        When I query HEAD "/deployments"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario: get a specific deployment
        Given there are deployments:
            | id    | user  | status        | duration  |
            | 1     | foo   | pending       | 1         |
            | 2     | bar   | queued        | 0         |
            | 3     | baz   | inprogress    | 20        |
        When I query HEAD "/deployments/2"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario Outline: specify limit and/or last queries
        Given there are deployments:
            | id    | user  | status        |
            | 1     | foo   | pending       |
            | 2     | bar   | queued        |
            | 3     | baz   | inprogress    |
            | 4     | bar   | queued        |
            | 5     | baz   | inprogress    |
        When I query HEAD "/deployments?limit=<limit>&start=<start>"
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
