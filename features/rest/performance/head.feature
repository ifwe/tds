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

Feature: REST API performance HEAD
    As a developer
    I want to test my GET query
    So that I can be sure that my query is not malformed

    Background:
        Given I have a cookie with user permissions

    @rest
    Scenario: get with no data
        When I query HEAD "/performance"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario: get with data
        Given there is an application with name="app1"
        And there is an environment with name="dev"
        And there is a deploy target with name="tier1"
        And there are hosts:
            | name  | env   |
            | host1 | dev   |
        And there are packages:
            | version   | revision  | created               | status        |
            | 1         | 1         | 2016-01-02 01:00:00   | failed        |
            | 2         | 2         | 2016-01-02 02:00:00   | completed     |
            | 3         | 3         | 2016-01-02 03:00:00   | removed       |
            | 4         | 4         | 2016-01-02 04:00:00   | pending       |
            | 5         | 5         | 2016-01-02 04:00:01   | processing    |
        And there are deployments:
            | id    | user  | status        | declared              |
            | 1     | foo   | pending       | 2016-01-03 01:00:00   |
            | 2     | foo   | failed        | 2016-01-03 02:00:00   |
            | 3     | foo   | pending       | 2016-01-03 03:00:00   |
            | 4     | foo   | inprogress    | 2016-01-03 04:00:00   |
            | 5     | foo   | queued        | 2016-01-03 04:00:01   |
        And there are tier deployments:
            | id    | user  | status        | realized              | deployment_id | package_id    | app_id    | environment_id    |
            | 1     | foo   | complete      | 2016-01-01 01:00:00   | 1             | 1             | 1         | 1                 |
            | 2     | foo   | incomplete    | 2016-01-01 02:00:00   | 1             | 1             | 1         | 1                 |
            | 3     | foo   | inprogress    | 2016-01-01 03:00:00   | 1             | 1             | 1         | 1                 |
            | 4     | foo   | pending       | 2016-01-01 04:00:00   | 1             | 1             | 1         | 1                 |
            | 5     | foo   | validated     | 2016-01-01 04:00:01   | 1             | 1             | 1         | 1                 |
        And there are host deployments:
            | id    | user  | status    | realized              | deployment_id | package_id    | host_id   |
            | 1     | foo   | ok        | 2016-01-30 01:00:00   | 1             | 1             | 1         |
            | 2     | foo   | failed    | 2016-01-30 02:00:00   | 1             | 1             | 1         |
            | 3     | foo   | pending   | 2016-01-30 03:00:00   | 1             | 1             | 1         |
            | 4     | foo   | ok        | 2016-01-30 04:00:00   | 1             | 1             | 1         |
            | 5     | foo   | ok        | 2016-01-30 04:00:01   | 1             | 1             | 1         |
        When I query HEAD "/performance"
        Then the response code is 200
        And the response body is empty
