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

Feature: PUT deployment(s) from the REST API
    As a developer
    I want to update deployments
    So that I can modify my deployments

    Background:
        Given I have a cookie with user permissions
        And there is an application with pkg_name="app1"
        And there are packages:
            | version   | revision  | status    |
            | 1         | 1         | completed |
            | 1         | 2         | completed |
            | 2         | 3         | completed |
            | 2         | 4         | completed |
        And there is an application with pkg_name="app2"
        And there are packages:
            | version   | revision  | status    |
            | 3         | 5         | completed |
            | 3         | 6         | completed |
        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | pending   |
            | 2     | bar   | pending   |
            | 3     | baz   | pending   |
        And there is an environment with name="dev"
        And there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 1     | 1             | 1         | pending   | foo   | 1             |

    @rest
    Scenario: put a deployment
        When I query PUT "/deployments/1?status=queued&delay=10"
        Then the response code is 200
        And the response is an object with id=1,status="queued",delay=10
        And there is a deployment with id=1,status="queued",delay=10
        And there is no deployment with id=1,status="pending",delay=0

    @rest
    Scenario: attempt to queue a deployment with no tier or host deployments
        When I query PUT "/deployments/2?status=queued"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                               |
            | query     | status    | Cannot queue deployment with no tier or host deployments. |
        And there is a deployment with id=2,status="pending"
        And there is no deployment with status="queued"

    @rest
    Scenario Outline: attempt to change status to something other than canceled, pending, queued
        When I query PUT "/deployments/1?status=<status>"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                               |
            | query     | status    | Users cannot change status to <status>.   |
        And there is a deployment with id=1,status="pending"
        And there is no deployment with status="<status>"

        Examples:
            | status        |
            | complete      |
            | failed        |
            | stopped       |
            | inprogress    |

    @rest
    Scenario Outline: attempt an illegal status change
        Given there are deployments:
            | id    | user  | status    |
            | 4     | foo   | <old>     |
        When I query PUT "/deployments/4?status=<new>"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                               |
            | query     | status    | Cannot change status to <new> from <old>. |
        And there is a deployment with id=4,status="<old>"
        And there is no deployment with id=4,status="<new>"

        Examples:
            | old           | new       |
            | canceled      | queued    |
            | inprogress    | queued    |
            | complete      | queued    |
            | queued        | pending   |
            | inprogress    | pending   |
            | failed        | pending   |
            | stopped       | pending   |
            | canceled      | pending   |
            | complete      | pending   |
            | pending       | canceled  |
            | failed        | canceled  |
            | complete      | canceled  |
            | stopped       | canceled  |

    @rest
    Scenario Outline: attempt to queue a deployment for a host that has an ongoing deployment
        Given there are deployments:
            | id    | user  | status        |
            | 4     | foo   | <dep_stat>    |
        And there are host deployments:
            | id    | deployment_id | host_id   | status        | user  | package_id    |
            | 3     | 3             | 1         | pending       | foo   | 1             |
            | 4     | 4             | 1         | <host_stat>   | foo   | 1             |
        When I query PUT "/deployments/3?status=queued"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                           |
            | query     | status    | Cannot queue deployment. There are currently other queued or in progress deployments for host host1.  |
        And there is a deployment with id=3,status="pending"
        And there is no deployment with id=3,status="queued"

        Examples:
            | dep_stat      | host_stat     |
            | queued        | pending       |
            | inprogress    | pending       |
            | inprogress    | inprogress    |
            | inprogress    | ok            |
            | inprogress    | failed        |

    @rest
    Scenario Outline: attempt to queue a deployment whose package hasn't been validated in the previous environment
        Given there is an environment with name="staging"
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are deployments:
            | id    | user  | status    |
            | 4     | foo   | pending   |
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 1     | 3             | 2         | pending   | foo   | 1                 | 1             |
            | 2     | 4             | 2         | pending   | foo   | 2                 | 3             |
        When I query PUT "/deployments/4?status=queued&<query>"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                                                           |
            | query     | status    | Package with ID 3 has not been validated in the dev environment for tier tier1 with ID 2. Please use force=true to force deployment.  |
        And there is a deployment with id=4,status="pending"
        And there is no deployment with id=4,status="queued"

        Examples:
            | query         |
            |               |
            | force=0       |
            | force=false   |
            | force=False   |

    @rest
    Scenario Outline: force deployment with validation in previous environment
        Given there is an environment with name="staging"
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are deployments:
            | id    | user  | status    |
            | 4     | foo   | pending   |
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 1     | 3             | 2         | pending   | foo   | 1                 | 1             |
            | 2     | 4             | 2         | pending   | foo   | 2                 | 3             |
        When I query PUT "/deployments/4?status=queued&force=<force>"
        Then the response code is 200
        And the response is an object with id=4,status="queued"
        And there is a deployment with id=4,status="queued"
        And there is no deployment with id=4,status="pending"

        Examples:
            | force |
            | true  |
            | 1     |
            | True  |

    @rest
    Scenario: pass a non-Boolean for force
        Given there is an environment with name="staging"
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are deployments:
            | id    | user  | status    |
            | 4     | foo   | pending   |
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 1     | 3             | 2         | validated | foo   | 1                 | 3             |
            | 2     | 4             | 2         | pending   | foo   | 2                 | 3             |
        When I query PUT "/deployments/4?status=queued&force=foo"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                                                                                                       |
            | query     | force | Value foo for argument force is not a Boolean. Valid Boolean formats: (0, 1, 'true', 'false', 'True', 'False').   |
        And there is a deployment with id=4,status="pending"
        And there is no deployment with id=4,status="queued"

    @rest
    Scenario: queue a deployment
        When I query PUT "/deployments/1?status=queued"
        Then the response code is 200
        And the response is an object with id=1,status="queued"
        And there is a deployment with id=1,status="queued"

    @rest
    Scenario: attempt to modify a deployment that doesn't exist
        When I query PUT "/deployments/500?status=queued"
        Then the response code is 404
        And the response contains errors:
            | location  | name  | description                               |
            | path      | id    | Deployment with ID 500 does not exist.    |

    @rest
    Scenario Outline: attempt to queue a deployment with a host deployment whose package isn't complete
        Given there are packages:
            | version   | revision  | status    |
            | 4         | 1         | <status>  |
        And there are deployments:
            | id    | user  | status    |
            | 4     | foo   | pending   |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 3     | 4             | 1         | pending   | foo   | 7             |
        When I query PUT "/deployments/4?status=queued"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                                                                                       |
            | query     | status    | Package with ID 7 for host deployment with ID 3 (for host with ID 3) is not completed. Please wait and verify that the package is completed before re-attempting. |
        And there is no deployment with id=4,status="queued"
        And there is a deployment with id=4,status="pending"

        Examples:
            | status        |
            | pending       |
            | processing    |
            | failed        |
            | removed       |

    @rest
    Scenario Outline: attempt to queue a deployment with a tier deployment whose package isn't complete
        Given there are packages:
            | version   | revision  | status    |
            | 4         | 1         | <status>  |
        And there are deployments:
            | id    | user  | status    |
            | 4     | foo   | pending   |
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | package_id    | environment_id    |
            | 1     | 4             | 1         | pending   | foo   | 7             | 1                 |
        When I query PUT "/deployments/4?status=queued"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                                                                                       |
            | query     | status    | Package with ID 7 for tier deployment with ID 1 (for tier with ID 1) is not completed. Please wait and verify that the package is completed before re-attempting. |
        And there is no deployment with id=4,status="queued"
        And there is a deployment with id=4,status="pending"

        Examples:
            | status        |
            | pending       |
            | processing    |
            | failed        |
            | removed       |
