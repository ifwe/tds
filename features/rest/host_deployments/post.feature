Feature: POST host deployment(s) from the REST API
    As a developer
    I want to add host deployments
    So that I can put my software on hosts

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

    @rest
    Scenario: post a host deployment
        When I query POST "/host_deployments?deployment_id=1&host_id=1"
        Then the response code is 201
        And the response is an object with deployment_id=1,host_id=1,id=1,user="testuser"
        And there is a host deployment with deployment_id=1,host_id=1,id=1,user="testuser"

    @rest
    Scenario: omit required field
        When I query POST "/host_deployments?deployment_id=1"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                   |
            | query     |       | host_id is a required field.  |
        And there is no host deployment with deployment_id=1,id=1

    @rest
    Scenario Outline: attempt to set the status to not pending
        When I query POST "/host_deployments?deployment_id=1&host_id=1&status=<status>"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                       |
            | query     | status    | Status must be pending for new host deployments.  |
        And there is no host deployment with deployment_id=1,host_id=1,status="<status>"

        Examples:
            | status        |
            | inprogress    |
            | failed        |
            | ok            |

    @rest
    Scenario: attempt to violate a unique constraint
        Given there are host deployments:
            | id    | deployment_id | host_id   | status        | user  |
            | 1     | 1             | 1         | pending       | foo   |
        When I query POST "/host_deployments?id=1&deployment_id=1&host_id=1"
        Then the response code is 409
        And the response contains errors:
            | location  | name  | description                                                                   |
            | query     | id    | Unique constraint violated. A host deployment with this ID already exists.    |
