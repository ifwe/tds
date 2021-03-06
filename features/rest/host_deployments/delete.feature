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

Feature: DELETE host deployment(s) from the REST API
    As a developer
    I want to delete my pending host deployments whose deployment is also pending
    So that I can remove host deployments added by mistake

    Background:
        Given I have a cookie with user permissions
        And there is an application with pkg_name="app1"
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
            | 1         | 2         |
        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | pending   |
        And there is an environment with name="dev"
        And there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 1     | 1             | 1         | pending   | foo   | 1             |

    @rest
    Scenario: attempt to delete a host deployment that doesn't exist
        When I query DELETE "/host_deployments/500"
        Then the response code is 404
        And the response contains errors:
            | location  | name  | description                                   |
            | path      | id    | Host deployment with ID 500 does not exist.   |

    @rest
    Scenario: delete a pending host deployment whose deployment is also pending
        When I query DELETE "/host_deployments/1"
        Then the response code is 200
        And the response is an object with id=1,deployment_id=1,host_id=1,status="pending",user="foo"
        And there is no host deployment with id=1,deployment_id=1,host_id=1,status="pending",user="foo"

    @rest
    Scenario Outline: attempt to delete a host deployment whose deployment is non-pending
        Given there are deployments:
            | id    | user  | status    |
            | 2     | foo   | <status>  |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 2     | 2             | 2         | pending   | foo   | 1             |
        When I query DELETE "/host_deployments/2"
        Then the response code is 403
        And the response contains errors:
            | location  | name  | description                                                           |
            | path      | id    | Cannot delete host deployment whose deployment is no longer pending.  |
        And there is a host deployment with id=2,deployment_id=2,host_id=2,status="pending",user="foo"

        Examples:
            | status        |
            | queued        |
            | inprogress    |
            | failed        |
            | complete      |
            | canceled      |
            | stopped       |

    @rest
    Scenario Outline: attempt to delete a host deployment that's a part of a tier deployment without cascade
        Given there is a deploy target with name="tier1"
        And there are hosts:
            | name  | env   | app_id    |
            | host3 | dev   | 1         |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 2     | 1             | 3         | pending   | foo   | 1             |
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 1     | 1             | 1         | pending   | foo   | 1                 | 1             |
        When I query DELETE "/host_deployments/2?<query>"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                                                                                   |
            | query     |           | Cannot delete a host deployment that is part of a tier deployment. Please use cascade=true to delete this host deployment and its associated tier deployment. |
            | url       | to_delete | {'tier_deployment': 1}                                                                                                                                          |
        And there is a host deployment with id=2
        And there is a tier deployment with id=1

        Examples:
            | query         |
            |               |
            | cascade=0     |
            | cascade=false |
            | cascade=False |

    @rest
    Scenario Outline: delete a host deployment associated with a tier deployment with cascade
        Given there is a deploy target with name="tier1"
        And there are hosts:
            | name  | env   | app_id    |
            | host3 | dev   | 1         |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 2     | 1             | 3         | pending   | foo   | 1             |
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 1     | 1             | 1         | pending   | foo   | 1                 | 1             |
        When I query DELETE "/host_deployments/2?<query>"
        Then the response code is 200
        And there is no host deployment with id=2
        And there is no tier deployment with id=1

        Examples:
            | query         |
            | cascade=1     |
            | cascade=true  |
            | cascade=True  |
