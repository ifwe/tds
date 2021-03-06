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

Feature: HEAD most recent deployment of an application on a given host
    As a user
    I want to test my GET query
    So that I can be sure my query is not malformed

    Background:
        Given I have a cookie with user permissions
        And there is an environment with name="dev"
        And there is an application with name="app1"
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
            | 1         | 2         |
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are hosts:
            | name  | app_id    | env   |
            | host1 | 2         | dev   |
            | host2 | 2         | dev   |
            | host3 | 3         | dev   |
        And there are projects:
            | name  |
            | proj1 |
        And the tier "tier1" is associated with the application "app1" for the project "proj1"

    @rest
    Scenario Outline: get for an application that doesn't exist
        When I query HEAD "/applications/<select>/hosts/host1"
        Then the response code is 404
        And the response body is empty

        Examples:
            | select    |
            | noexist   |
            | 500       |

    @rest
    Scenario Outline: get for a host that doesn't exist
        When I query HEAD "/applications/app1/hosts/<select>"
        Then the response code is 404
        And the response body is empty

        Examples:
            | select    |
            | noexist   |
            | 500       |

    @rest
    Scenario Outline: get for a host whose tier isn't associated with the application
        When I query HEAD "/applications/<a_select>/hosts/<h_select>"
        Then the response code is 403
        And the response body is empty

        Examples:
            | a_select  | h_select  |
            | 2         | host3     |
            | app1      | 3         |

    @rest
    Scenario: get for a host that hasn't had any deployments of the application
        When I query HEAD "/applications/app1/hosts/host1"
        Then the response code is 404
        And the response body is empty

    @rest
    Scenario Outline: get for a host that hasn't had any complete deployments of the application
        Given there are deployments:
            | id    | user  | status    |
            | 1     | foo   | complete  |
        And there are host deployments:
            | id    | deployment_id | status    | user  | host_id   | package_id    |
            | 1     | 1             | <status>  | foo   | 1         | 1             |
        When I query HEAD "/applications/app1/hosts/host1"
        Then the response code is 404
        And the response body is empty

        Examples:
            | status        |
            | pending       |
            | inprogress    |
            | failed        |

    @rest
    Scenario Outline: get the most recent host deployment for a given host
        Given there are deployments:
            | id    | user  | status    |
            | 1     | foo   | complete  |
        And there are host deployments:
            | id    | deployment_id | status    | user  | host_id   | package_id    |
            | 1     | 1             | ok        | foo   | 1         | 1             |
        And I wait 1 seconds
        And there are host deployments:
            | id    | deployment_id | status    | user  | host_id   | package_id    |
            | 2     | 1             | <status>  | foo   | 1         | 2             |
        When I query HEAD "/applications/app1/hosts/host1"
        Then the response code is 200
        And the response body is empty

        Examples:
            | status        |
            | pending       |
            | inprogress    |
            | failed        |
            | ok            |

    @rest
    Scenario: specify select query
        Given there are deployments:
            | id    | user  | status    |
            | 1     | foo   | complete  |
        And there are host deployments:
            | id    | deployment_id | status    | user  | host_id   | package_id    |
            | 1     | 1             | ok        | foo   | 1         | 1             |
        And I wait 1 seconds
        And there are host deployments:
            | id    | deployment_id | status    | user  | host_id   | package_id    |
            | 2     | 1             | pending   | foo   | 1         | 2             |
        When I query HEAD "/applications/app1/hosts/host1?select=id,deployment_id"
        Then the response code is 200
        And the response body is empty
