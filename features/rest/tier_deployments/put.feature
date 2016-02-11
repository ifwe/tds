Feature: PUT tier deployment(s) from the REST API
    As a developer
    I want to update tier deployments
    So that I can modify my tier deployments

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
        And there is a deploy target with name="tier2"
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 1     | 1             | 2         | pending   | foo   | 1                 | 1             |
        And the tier "tier1" is associated with the application "app1" for the project "proj1"
        And the tier "tier2" is associated with the application "app1" for the project "proj1"

    @rest
    Scenario: put a tier deployment
        When I query PUT "/tier_deployments/1?tier_id=3"
        Then the response code is 200
        And the response is an object with id=1,tier_id=3
        And there is a tier deployment with id=1,app_id=3
        And there is no tier deployment with id=1,deployment_id=1,app_id=2,status="pending",user="foo"

    @rest
    Scenario: pass a tier_id for a tier that doesn't exist
        When I query PUT "/tier_deployments/1?tier_id=500"
        Then the response code is 400
        And the response contains errors:
            | location  | name      | description                   |
            | query     | tier_id   | No tier with ID 500 exists.   |
        And there is no tier deployment with id=1,app_id=500
        And there is a tier deployment with id=1,app_id=2

    @rest
    Scenario: pass an environment_id for an environment that doesn't exist
        When I query PUT "/tier_deployments/1?environment_id=500"
        Then the response code is 400
        And the response contains errors:
            | location  | name              | description                           |
            | query     | environment_id    | No environment with ID 500 exists.    |
        And there is no tier deployment with id=1,environment_id=500
        And there is a tier deployment with id=1,environment_id=1

    @rest
    Scenario: change environment for a tier with hosts associated
        Given there is an environment with name="staging"
        And there are hosts:
            | name  | env       | app_id    |
            | host1 | dev       | 2         |
            | host2 | dev       | 2         |
            | host3 | dev       | 3         |
            | host4 | staging   | 2         |
            | host5 | staging   | 3         |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 1     | 1             | 1         | pending   | foo   | 1             |
            | 2     | 1             | 2         | pending   | foo   | 1             |
        When I query PUT "/tier_deployments/1?environment_id=2"
        Then the response code is 200
        And the response is an object with id=1,environment_id=2
        And there is a tier deployment with id=1,environment_id=2
        And there is a host deployment with host_id=4,deployment_id=1
        And there is no host deployment with host_id=1,deployment_id=1
        And there is no host deployment with host_id=2,deployment_id=1
        And there is no host deployment with host_id=3,deployment_id=1
        And there is no host deployment with host_id=5,deployment_id=1

    @rest
    Scenario: change package for a tier with hosts associated
        Given there is an environment with name="staging"
        And there are hosts:
            | name  | env       | app_id    |
            | host1 | dev       | 2         |
            | host2 | dev       | 2         |
            | host3 | dev       | 3         |
            | host4 | staging   | 2         |
            | host5 | staging   | 3         |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 1     | 1             | 1         | pending   | foo   | 1             |
            | 2     | 1             | 2         | pending   | foo   | 1             |
        When I query PUT "/tier_deployments/1?package_id=2"
        Then the response code is 200
        And the response is an object with id=1,package_id=2
        And there is a tier deployment with id=1,package_id=2
        And there is a host deployment with host_id=1,deployment_id=1,package_id=2
        And there is no host deployment with host_id=1,deployment_id=1,package_id=1

    @rest
    Scenario: change tier_id from a tier with hosts to another with hosts
        Given there are hosts:
            | name  | env   | app_id    |
            | host1 | dev   | 2         |
            | host2 | dev   | 2         |
            | host3 | dev   | 3         |
            | host4 | dev   | 3         |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 1     | 1             | 1         | pending   | foo   | 1             |
            | 2     | 1             | 2         | pending   | foo   | 1             |
        When I query PUT "/tier_deployments/1?tier_id=3"
        Then the response code is 200
        And the response is an object with id=1,tier_id=3,environment_id=1,deployment_id=1
        And there is a tier deployment with id=1,app_id=3,environment_id=1,deployment_id=1
        And there is a host deployment with host_id=3,deployment_id=1
        And there is a host deployment with host_id=4,deployment_id=1
        And there is no host deployment with host_id=1,deployment_id=1
        And there is no host deployment with host_id=2,deployment_id=1

    @rest
    Scenario: change tier_id and environment_id s.t. host deps are deleted and created
        Given there is an environment with name="staging"
        And there are hosts:
            | name  | env       | app_id    |
            | host1 | dev       | 2         |
            | host2 | dev       | 2         |
            | host3 | staging   | 3         |
            | host4 | staging   | 3         |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 1     | 1             | 1         | pending   | foo   | 1             |
            | 2     | 1             | 2         | pending   | foo   | 1             |
        When I query PUT "/tier_deployments/1?tier_id=3&environment_id=2"
        Then the response code is 200
        And the response is an object with id=1,tier_id=3,environment_id=2,deployment_id=1
        And there is a tier deployment with id=1,app_id=3,environment_id=2,deployment_id=1
        And there is a host deployment with host_id=3,deployment_id=1
        And there is a host deployment with host_id=4,deployment_id=1
        And there is no host deployment with host_id=1,deployment_id=1
        And there is no host deployment with host_id=2,deployment_id=1

    @rest
    Scenario Outline: attempt to modify a tier deployment whose deployment is queued or inprogress
        Given there are deployments:
            | id    | user  | status    |
            | 2     | foo   | <status>  |
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 2     | 2             | 3         | pending   | foo   | 1                 | 1             |
        When I query PUT "/tier_deployments/2?tier_id=2"
        Then the response code is 403
        And the response contains errors:
            | location  | name  | description                                                                       |
            | path      | id    | Users cannot modify tier deployments whose deployments are in progress or queued. |
        And there is no tier deployment with id=2,app_id=2
        And there is a tier deployment with id=2,app_id=3

        Examples:
            | status        |
            | queued        |
            | inprogress    |

    @rest
    Scenario Outline: attempt to change attribute other than status for tier deployment whose deployment is non-pending
        Given there are deployments:
            | id    | user  | status    |
            | 2     | foo   | <status>  |
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 2     | 2             | 3         | pending   | foo   | 1                 | 1             |
        When I query PUT "/tier_deployments/2?tier_id=2"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                           |
            | query     | tier_id   | Users can only modify status for tier deployments whose deployments are non-pending.  |
        And there is no tier deployment with id=2,app_id=2
        And there is a tier deployment with id=2,app_id=3

        Examples:
            | status    |
            | complete  |
            | canceled  |
            | canceled  |
            | stopped   |

    @rest
    Scenario Outline: attempt to modify a tier deployment status from pending, inprogress, or incomplete
        Given there are deployments:
            | id    | user  | status    |
            | 2     | foo   | complete  |
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 2     | 2             | 3         | <status>  | foo   | 1                 | 1             |
        When I query PUT "/tier_deployments/2?status=validated"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                   |
            | query     | status    | Users cannot change the status of tier deployments from pending, inprogress, or incomplete.   |
        And there is no tier deployment with id=2,app_id=2
        And there is a tier deployment with id=2,app_id=3

        Examples:
            | status        |
            | pending       |
            | inprogress    |
            | incomplete    |

    @rest
    Scenario Outline: attempt to modify a tier deployment status from pending, inprogress, or incomplete
        Given there are deployments:
            | id    | user  | status    |
            | 2     | foo   | complete  |
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 2     | 2             | 3         | complete  | foo   | 1                 | 1             |
        When I query PUT "/tier_deployments/2?status=<status>"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                               |
            | query     | status    | Users cannot change the status of tier deployments to pending, inprogress, or incomplete. |
        And there is no tier deployment with id=2,app_id=2
        And there is a tier deployment with id=2,app_id=3

        Examples:
            | status        |
            | pending       |
            | inprogress    |
            | incomplete    |

    @rest
    Scenario: attempt to violate (deployment_id, tier_id, package_id) unique together constraint
        Given there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 2     | 1             | 3         | pending   | foo   | 1                 | 1             |
        When I query PUT "/tier_deployments/2?tier_id=2"
        Then the response code is 409
        And the response contains errors:
            | location  | name          | description                                                                                                                   |
            | query     | package_id    | ('deployment_id', 'tier_id', 'package_id') are unique together. Another tier deployment with these attributes already exists. |
        And there is no tier deployment with id=2,deployment_id=1,app_id=2,package_id=1
        And there is a tier deployment with id=2,deployment_id=1,app_id=3,package_id=1

    @rest
    Scenario: attempt to modify a tier deployment that doesn't exist
        When I query PUT "/tier_deployments/500?tier_id=2"
        Then the response code is 404
        And the response contains errors:
            | location  | name  | description                                   |
            | path      | id    | Tier deployment with ID 500 does not exist.   |

    @rest
    Scenario: attempt to modify environment_id to one that conflicts with the deployment's environment
        Given there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 2     | 1             | 3         | pending   | foo   | 1                 | 1             |
        And there is an environment with name="staging"
        And there are hosts:
            | name  | env   |
            | host1 | dev   |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 1     | 1             | 1         | pending   | foo   | 1             |
        When I query PUT "/tier_deployments/2?environment_id=2"
        Then the response code is 409
        And the response contains errors:
            | location  | name              | description                                                                                                                                                       |
            | query     | environment_id    | Cannot deploy to different environments with same deployment. There is a tier deployment associated with this deployment with ID 1 and environment development.   |
            | query     | environment_id    | Cannot deploy to different environments with same deployment. There is a host deployment associated with this deployment with ID 1 and environment development.   |
        And there is no tier deployment with id=2,environment_id=2
        And there is a tier deployment with id=2,environment_id=1

    @rest
    Scenario: attempt to modify deployment_id s.t. environments conflict
        Given there is an environment with name="staging"
        And there are deployments:
            | id    | user  | status    |
            | 2     | foo   | pending   |
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 2     | 2             | 3         | pending   | foo   | 2                 | 1             |
        And there are hosts:
            | name  | env       | app_id    |
            | host1 | staging   | 3         |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 1     | 2             | 1         | pending   | foo   | 1             |
        When I query PUT "/tier_deployments/1?deployment_id=2"
        Then the response code is 409
        And the response contains errors:
            | location  | name          | description                                                                                                                                                   |
            | query     | deployment_id | Cannot deploy to different environments with same deployment. There is a tier deployment associated with this deployment with ID 2 and environment staging.   |
            | query     | deployment_id | Cannot deploy to different environments with same deployment. There is a host deployment associated with this deployment with ID 1 and environment staging.   |
        And there is no tier deployment with id=1,deployment_id=2
        And there is a tier deployment with id=1,deployment_id=1

    @rest
    Scenario: attempt to modify deployment_id and environment_id s.t. environments conflict
        Given there is an environment with name="staging"
        And there are deployments:
            | id    | user  | status    |
            | 2     | foo   | pending   |
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 2     | 2             | 3         | pending   | foo   | 1                 | 1             |
        And there are hosts:
            | name  | env   | app_id    |
            | host1 | dev   | 3         |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 1     | 2             | 1         | pending   | foo   | 1             |
        When I query PUT "/tier_deployments/1?deployment_id=2&environment_id=2"
        Then the response code is 409
        And the response contains errors:
            | location  | name              | description                                                                                                                                                       |
            | query     | environment_id    | Cannot deploy to different environments with same deployment. There is a tier deployment associated with this deployment with ID 2 and environment development.   |
            | query     | environment_id    | Cannot deploy to different environments with same deployment. There is a host deployment associated with this deployment with ID 1 and environment development.   |
        And there is no tier deployment with id=1,deployment_id=2,environment_id=2
        And there is a tier deployment with id=1,deployment_id=1,environment_id=1

    @rest
    Scenario Outline: attempt to deploy to a tier that isn't associated with the package's application
        Given there is an application with pkg_name="app2"
        And there are packages:
            | version   | revision  |
            | 2         | 3         |
        And there is a deploy target with name="tier3"
        When I query PUT "/tier_deployments/1?<query>"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                   |
            | query     | <name>    | Tier <tier> is not associated with the application <app> for any projects.    |
        And there is no tier deployment with id=1,<props>

        Examples:
            | query                     | name          | tier  | app   | props                 |
            | tier_id=4                 | tier_id       | tier3 | app1  | app_id=4              |
            | tier_id=4&package_id=3    | tier_id       | tier3 | app2  | app_id=4,package_id=2 |
            | package_id=3              | package_id    | tier1 | app2  | package_id=3          |
