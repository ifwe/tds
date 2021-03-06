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

Feature: PUT host deployment(s) from the REST API
    As a developer
    I want to update host deployments
    So that I can modify my host deployments

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
        And there are projects:
            | name  |
            | proj1 |
        And there is an environment with name="dev"
        And there is a deploy target with name="tier1"
        And the tier "tier1" is associated with the application "app1" for the project "proj1"
        And there are hosts:
            | name  | env   | app_id    |
            | host1 | dev   | 2         |
            | host2 | dev   | 2         |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 1     | 1             | 1         | pending   | foo   | 1             |

    @rest
    Scenario: put a host deployment
        When I query PUT "/host_deployments/1?host_id=2"
        Then the response code is 200
        And the response is an object with host_id=2
        And there is a host deployment with host_id=2
        And there is no host deployment with id=1,deployment_id=1,host_id=1,status="pending",user="foo"

    @rest
    Scenario: pass a host_id for a host that doesn't exist
        When I query PUT "/host_deployments/1?host_id=500"
        Then the response code is 400
        And the response contains errors:
            | location  | name      | description                   |
            | query     | host_id   | No host with ID 500 exists.   |
        And there is no host deployment with id=1,host_id=500
        And there is a host deployment with id=1,host_id=1

    @rest
    Scenario Outline: attempt to modify a host deployment whose deployment is non-pending
        Given there are deployments:
            | id    | user  | status    |
            | 2     | foo   | <status>  |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 2     | 2             | 1         | pending   | foo   | 1             |
        When I query PUT "/host_deployments/2?host_id=2"
        Then the response code is 403
        And the response contains errors:
            | location  | name  | description                                                                   |
            | path      | id    | Users cannot modify host deployments whose deployments are no longer pending. |
        And there is no host deployment with id=2,host_id=2
        And there is a host deployment with id=2,host_id=1

        Examples:
            | status        |
            | queued        |
            | inprogress    |
            | complete      |
            | failed        |
            | canceled      |
            | stopped       |

    @rest
    Scenario: attempt to modify status
        When I query PUT "/host_deployments/1?status=inprogress"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                           |
            | query     | status    | Users cannot change the status of host deployments.   |
        And there is no host deployment with id=1,status="inprogress"
        And there is a host deployment with id=1,status="pending"

    @rest
    Scenario: attempt to violate (deployment_id, host_id, package_id) unique together constraint
        Given there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 2     | 1             | 2         | pending   | foo   | 1             |
        When I query PUT "/host_deployments/2?host_id=1"
        Then the response code is 409
        And the response contains errors:
            | location  | name          | description                                                                                                       |
            | query     | package_id    | ('deployment_id', 'host_id', 'package_id') are unique together. Another host deployment with these attributes already exists.   |
        And there is no host deployment with id=2,deployment_id=1,host_id=1,package_id=1
        And there is a host deployment with id=2,deployment_id=1,host_id=2,package_id=1

    @rest
    Scenario: attempt to modify a host deployment that doesn't exist
        When I query PUT "/host_deployments/500?host_id=2"
        Then the response code is 404
        And the response contains errors:
            | location  | name  | description                                   |
            | path      | id    | Host deployment with ID 500 does not exist.   |

    @rest
    Scenario: attempt to modify host_id to a host in a different environment from that of the deployment
        Given there is a deploy target with name="tier1"
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 1     | 1             | 1         | pending   | foo   | 1                 | 1             |
        And there is an environment with name="staging"
        And there are hosts:
            | name  | env       | app_id    |
            | host3 | staging   | 2         |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 2     | 1             | 2         | pending   | foo   | 1             |
        When I query PUT "/host_deployments/1?host_id=3"
        Then the response code is 409
        And the response contains errors:
            | location  | name      | description                                                                                                                                                       |
            | query     | host_id   | Cannot deploy to different environments with same deployment. There is a tier deployment associated with this deployment with ID 1 and environment development.   |
            | query     | host_id   | Cannot deploy to different environments with same deployment. There is a host deployment associated with this deployment with ID 2 and environment development.   |
        And there is no host deployment with id=1,host_id=3
        And there is a host deployment with id=1,host_id=1

    @rest
    Scenario: attempt to modify deployment_id to a deployment with a different environment
        Given there is a deploy target with name="tier1"
        And there are deployments:
            | id    | user  | status    |
            | 2     | foo   | pending   |
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 1     | 1             | 1         | pending   | foo   | 1                 | 1             |
        And there is an environment with name="staging"
        And there are hosts:
            | name  | env       | app_id    |
            | host3 | staging   | 2         |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 2     | 2             | 3         | pending   | foo   | 1             |
        When I query PUT "/host_deployments/2?deployment_id=1"
        Then the response code is 409
        And the response contains errors:
            | location  | name          | description                                                                                                                                                       |
            | query     | deployment_id | Cannot deploy to different environments with same deployment. There is a tier deployment associated with this deployment with ID 1 and environment development.   |
            | query     | deployment_id | Cannot deploy to different environments with same deployment. There is a host deployment associated with this deployment with ID 1 and environment development.   |
        And there is no host deployment with id=2,deployment_id=1
        And there is a host deployment with id=2,deployment_id=2

    @rest
    Scenario: attempt to modify host_id and deployment_id s.t. environments conflict
        Given there is a deploy target with name="tier1"
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 1     | 1             | 1         | pending   | foo   | 1                 | 1             |
        And there are deployments:
            | id    | user  | status    |
            | 2     | foo   | pending   |
        And there is an environment with name="staging"
        And there are hosts:
            | name  | env       | app_id    |
            | host3 | staging   | 2         |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 2     | 2             | 2         | pending   | foo   | 1             |
        When I query PUT "/host_deployments/2?deployment_id=1&host_id=3"
        Then the response code is 409
        And the response contains errors:
            | location  | name      | description                                                                                                                                                       |
            | query     | host_id   | Cannot deploy to different environments with same deployment. There is a tier deployment associated with this deployment with ID 1 and environment development.   |
            | query     | host_id   | Cannot deploy to different environments with same deployment. There is a host deployment associated with this deployment with ID 1 and environment development.   |
        And there is no host deployment with id=2,deployment_id=1,host_id=3
        And there is a host deployment with id=2,deployment_id=2,host_id=2

    @rest
    Scenario Outline: attempt to deploy to a host whose tier isn't associated with the package's application
        Given there is an application with pkg_name="app2"
        And there are packages:
            | version   | revision  |
            | 2         | 3         |
        And there is a deploy target with name="tier2"
        And there are hosts:
            | name  | env   | app_id    |
            | host3 | dev   | 3         |
        When I query PUT "/host_deployments/1?<query>"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                               |
            | query     | <name>    | Tier <tier> of host <host> is not associated with the application <app> for any projects. |
        And there is no host deployment with id=1,<props>

        Examples:
            | query                     | name          | tier  | host  | app   | props                     |
            | host_id=3                 | host_id       | tier2 | host3 | app1  | host_id=3                 |
            | host_id=3&package_id=3    | host_id       | tier2 | host3 | app2  | host_id=3,package_id=3    |
            | package_id=3              | package_id    | tier1 | host1 | app2  | package_id=3              |
