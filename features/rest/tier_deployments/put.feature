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
            | id    | user  | package_id    | status    |
            | 1     | foo   | 1             | pending   |
        And there is an environment with name="dev"
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    |
            | 1     | 1             | 1         | pending   | foo   | 1                 |

    @rest
    Scenario: put a tier deployment
        When I query PUT "/tier_deployments/1?tier_id=2"
        Then the response code is 200
        And the response is an object with id=1,tier_id=2
        And there is a tier deployment with id=1,app_id=2
        And there is no tier deployment with id=1,deployment_id=1,app_id=1,status="pending",user="foo"

    @rest
    Scenario: pass a tier_id for a tier that doesn't exist
        When I query PUT "/tier_deployments/1?tier_id=500"
        Then the response code is 400
        And the response contains errors:
            | location  | name      | description                   |
            | query     | tier_id   | No tier with ID 500 exists.   |
        And there is no tier deployment with id=1,app_id=500
        And there is a tier deployment with id=1,app_id=1

    @rest
    Scenario Outline: attempt to modify a tier deployment whose deployment is non-pending
        Given there are deployments:
            | id    | user  | package_id    | status    |
            | 2     | foo   | 1             | <status>  |
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    |
            | 2     | 2             | 1         | pending   | foo   | 1                 |
        When I query PUT "/tier_deployments/2?tier_id=2"
        Then the response code is 403
        And the response contains errors:
            | location  | name  | description                                                                   |
            | path      | id    | Users cannot modify tier deployments whose deployments are no longer pending. |
        And there is no tier deployment with id=2,app_id=2
        And there is a tier deployment with id=2,app_id=1

        Examples:
            | status        |
            | queued        |
            | inprogress    |
            | complete      |
            | failed        |
            | canceled      |
            | stopped       |

    @rest
    Scenario: attempt to violate a unique constraint
        Given there are deployments:
            | id    | user  | package_id    | status    |
            | 2     | foo   | 1             | pending   |
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    |
            | 2     | 2             | 1         | pending   | foo   | 1                 |
        When I query PUT "/tier_deployments/2?id=1"
        Then the response code is 409
        And the response contains errors:
            | location  | name  | description                                                                       |
            | query     | id    | Unique constraint violated. Another tier deployment with this ID already exists.  |
        And there is no tier deployment with id=1,deployment_id=2
        And there is a tier deployment with id=2,deployment_id=2

    @rest
    Scenario: attempt to modify status
        When I query PUT "/tier_deployments/1?status=inprogress"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                           |
            | query     | status    | Users cannot change the status of tier deployments.   |

    @rest
    Scenario: attempt to violate (deployment_id, tier_id) unique together constraint
        Given there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    |
            | 2     | 1             | 2         | pending   | foo   | 1                 |
        When I query PUT "/tier_deployments/2?tier_id=1"
        Then the response code is 409
        And the response contains errors:
            | location  | name      | description                                                                                                       |
            | query     | tier_id   | ('deployment_id', 'tier_id') are unique together. Another tier deployment with these attributes already exists.   |
        And there is no tier deployment with id=2,deployment_id=1,app_id=1
        And there is a tier deployment with id=2,deployment_id=1,app_id=2

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
            | id    | deployment_id | app_id    | status    | user  | environment_id    |
            | 2     | 1             | 2         | pending   | foo   | 1                 |
        And there is an environment with name="staging"
        And there are hosts:
            | name  | env   |
            | host1 | dev   |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  |
            | 1     | 1             | 1         | pending   | foo   |
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
            | id    | user  | package_id    | status    |
            | 2     | foo   | 1             | pending   |
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    |
            | 2     | 2             | 2         | pending   | foo   | 2                 |
        And there are hosts:
            | name  | env       |
            | host1 | staging   |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  |
            | 1     | 2             | 1         | pending   | foo   |
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
            | id    | user  | package_id    | status    |
            | 2     | foo   | 1             | pending   |
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    |
            | 2     | 2             | 2         | pending   | foo   | 1                 |
        And there are hosts:
            | name  | env   |
            | host1 | dev   |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  |
            | 1     | 2             | 1         | pending   | foo   |
        When I query PUT "/tier_deployments/1?deployment_id=2&environment_id=2"
        Then the response code is 409
        And the response contains errors:
            | location  | name              | description                                                                                                                                                       |
            | query     | environment_id    | Cannot deploy to different environments with same deployment. There is a tier deployment associated with this deployment with ID 2 and environment development.   |
            | query     | environment_id    | Cannot deploy to different environments with same deployment. There is a host deployment associated with this deployment with ID 1 and environment development.   |
        And there is no tier deployment with id=1,deployment_id=2,environment_id=2
        And there is a tier deployment with id=1,deployment_id=1,environment_id=1
