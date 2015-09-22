Feature: DELETE deployment(s) from the REST API
    As a developer
    I want to delete my pending deployments
    So that I can remove deployments added by mistake

    Background:
        Given I have a cookie with user permissions
        And there is an application with pkg_name="app1"
        And there are packages:
            | version   | revision  |
            | 1         | 1         |

    @rest
    Scenario: delete a pending deployment with no app or tier deployments
        Given there are deployments:
            | id    | user  | package_id    | status    |
            | 1     | baz   | 1             | pending   |
        When I query DELETE "/deployments/1"
        Then the response code is 200
        And the response is an object with id=1,user="baz",package_id=1,status="pending"
        And there is no deployment with id=1,user="baz",package_id=1,status="pending"

    @rest
    Scenario Outline: attempt to delete a non-pending deployment
        Given there are deployments:
            | id    | user  | package_id    | status    |
            | 1     | baz   | 1             | <status>  |
        When I query DELETE "/deployments/1"
        Then the response code is 403
        And the response contains errors:
            | location  | name  | description                                                                               |
            | url       | id    | Cannot delete a non-pending deployment. This deployment is currently in <status> status.  |
        And there is a deployment with id=1,user="baz",package_id=1,status="<status>"

        Examples:
            | status        |
            | queued        |
            | inprogress    |
            | failed        |
            | stopped       |
            | canceled      |
            | complete      |

    @rest
    Scenario Outline: attempt to delete a pending deployment with host and tier deployments without cascade
        Given there are deployments:
            | id    | user  | package_id    | status    |
            | 1     | baz   | 1             | pending   |
        And there is an environment with name="dev"
        And there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  |
            | 1     | 1             | 1         | pending   | foo   |
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    |
            | 1     | 1             | 1         | pending   | foo   | 1                 |
            | 2     | 1             | 2         | pending   | foo   | 1                 |
        When I query DELETE "/deployments/1?<query>"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                               |
            | url       | id        | Cannot delete deployment with host or tier deployments. Please use the cascade=true parameter to cascade. |
            | url       | to_delete | {'tier_deployments': [1, 2], 'host_deployments': [1]}                                                     |
        And there is a deployment with id=1,user="baz",package_id=1,status="pending"

        Examples:
            | query         |
            |               |
            | cascade=0     |
            | cascade=false |
            | cascade=False |

    @rest
    Scenario Outline: cascade deletes
        Given there are deployments:
            | id    | user  | package_id    | status    |
            | 1     | baz   | 1             | pending   |
        And there is an environment with name="dev"
        And there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  |
            | 1     | 1             | 1         | pending   | foo   |
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    |
            | 1     | 1             | 1         | pending   | foo   | 1                 |
            | 2     | 1             | 2         | pending   | foo   | 1                 |
        When I query DELETE "/deployments/1?cascade=<cascade>"
        Then the response code is 200
        And the response is an object with id=1,user="baz",package_id=1,status="pending"
        And there is no deployment with id=1,user="baz",package_id=1,status="pending"
        And there is no host deployment with id=1
        And there is no tier deployment with id=1
        And there is no tier deployment with id=2

        Examples:
            | cascade   |
            | 1         |
            | true      |
            | True      |

    @rest
    Scenario Outline: attempt to delete a deployment that doesn't exist
        Given there are deployments:
            | id    | user  | package_id    | status    |
            | 1     | foo   | 1             | pending   |
            | 2     | bar   | 1             | queued    |
        When I query DELETE "/deployments/3?<query>"
        Then the response code is 404
        And the response contains errors:
            | location  | name  | description                           |
            | path      | id    | Deployment with ID 3 does not exist.  |

        Examples:
            | query     |
            |           |
            | cascade=1 |
            | cascade=0 |
