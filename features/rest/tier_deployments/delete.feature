Feature: DELETE tier deployment(s) from the REST API
    As a developer
    I want to delete my pending tier deployments whose deployment is also pending
    So that I can remove tier deployments added by mistake

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
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 1     | 1             | 1         | pending   | foo   | 1                 | 1             |

    @rest
    Scenario: attempt to delete a tier deployment that doesn't exist
        When I query DELETE "/tier_deployments/500"
        Then the response code is 404
        And the response contains errors:
            | location  | name  | description                                   |
            | path      | id    | Tier deployment with ID 500 does not exist.   |

    @rest
    Scenario: delete a pending tier deployment whose deployment is also pending
        When I query DELETE "/tier_deployments/1"
        Then the response code is 200
        And the response is an object with id=1,deployment_id=1,tier_id=1,status="pending",user="foo"
        And there is no tier deployment with id=1,deployment_id=1,app_id=1,status="pending",user="foo"

    @rest
    Scenario Outline: attempt to delete a tier deployment whose deployment is non-pending
        Given there are deployments:
            | id    | user  | status    |
            | 2     | foo   | <status>  |
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 2     | 2             | 2         | pending   | foo   | 1                 | 1             |
        When I query DELETE "/tier_deployments/2"
        Then the response code is 403
        And the response contains errors:
            | location  | name  | description                                                           |
            | path      | id    | Cannot delete tier deployment whose deployment is no longer pending.  |
        And there is a tier deployment with id=2,deployment_id=2,app_id=2,status="pending",user="foo"

        Examples:
            | status        |
            | queued        |
            | inprogress    |
            | failed        |
            | complete      |
            | canceled      |
            | stopped       |
