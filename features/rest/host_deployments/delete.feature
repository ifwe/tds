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
            | id    | user  | package_id    | status    |
            | 1     | foo   | 1             | pending   |
        And there is an environment with name="dev"
        And there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  |
            | 1     | 1             | 1         | pending   | foo   |

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
            | id    | user  | package_id    | status    |
            | 2     | foo   | 1             | <status>  |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  |
            | 2     | 2             | 2         | pending   | foo   |
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
