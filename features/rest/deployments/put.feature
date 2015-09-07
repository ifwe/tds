Feature: PUT deployment(s) from the REST API
    As a developer
    I want to update deployments
    So that I can modify my deployments

    Background:
        Given I have a cookie with user permissions
        And there is an application with pkg_name="app1"
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
            | 1         | 2         |
            | 2         | 3         |
            | 2         | 4         |
        And there is an application with pkg_name="app2"
        And there are packages:
            | version   | revision  |
            | 3         | 5         |
            | 3         | 6         |
        And there are deployments:
            | id    | user  | package_id    | status    |
            | 1     | foo   | 1             | pending   |
            | 2     | bar   | 2             | pending   |
            | 3     | baz   | 3             | pending   |

    @rest
    Scenario Outline: put a deployment
        When I query PUT "/deployments/1?<query>"
        Then the response code is 200
        And the response is an object with <props>
        And there is a deployment with <props>
        And there is no deployment with <prev_props>

        Examples:
            | query             | props             | prev_props                |
            | package_id=2      | id=1,package_id=2 | id=1,package_id=1         |
            | id=9              | id=9,package_id=1 | id=1,package_id=1         |

    @rest
    Scenario: attempt to queue a deployment with no tier or host deployments
        When I query PUT "/deployments/1?status=queued"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                               |
            | query     | status    | Cannot queue deployment with no tier or host deployments. |
        And there is a deployment with id=1,status="pending"
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
            | id    | user  | package_id    | status    |
            | 4     | foo   | 4             | <old>     |
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
