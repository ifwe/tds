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
            | id    | user  | package_id    | status    |
            | 2     | foo   | 1             | <status>  |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  |
            | 2     | 2             | 1         | pending   | foo   |
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
    Scenario: attempt to violate a unique constraint
        Given there are deployments:
            | id    | user  | package_id    | status    |
            | 2     | foo   | 1             | pending   |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  |
            | 2     | 2             | 1         | pending   | foo   |
        When I query PUT "/host_deployments/2?id=1"
        Then the response code is 409
        And the response contains errors:
            | location  | name  | description                                                                       |
            | query     | id    | Unique constraint violated. Another host deployment with this ID already exists.  |

    @rest
    Scenario: attempt to modify status
        When I query PUT "/host_deployments/1?status=inprogress"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                           |
            | query     | status    | Users cannot change the status of host deployments.   |

    @rest
    Scenario: attempt to violate (deployment_id, host_id) unique together constraint
        Given there are host deployments:
            | id    | deployment_id | host_id   | status    | user  |
            | 2     | 1             | 2         | pending   | foo   |
        When I query PUT "/host_deployments/2?host_id=1"
        Then the response code is 409
        And the response contains errors:
            | location  | name      | description                                                                                                       |
            | query     | host_id   | ('deployment_id', 'host_id') are unique together. Another host deployment with these attributes already exists.   |
        And there is no host deployment with id=2,deployment_id=1,host_id=1
        And there is a host deployment with id=2,deployment_id=1,host_id=2

    @rest
    Scenario: attempt to modify a host deployment that doesn't exist
        When I query PUT "/host_deployments/500?host_id=2"
        Then the response code is 404
        And the response contains errors:
            | location  | name  | description                                   |
            | path      | id    | Host deployment with ID 500 does not exist.   |
