Feature: POST deployment(s) from the REST API
    As a developer
    I want to add deployments
    So that I can put my software on tiers

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

    @rest
    Scenario: post a deployment
        When I query POST "/deployments?package_id=1"
        Then the response code is 201
        And the response is an object with id=1,package_id=1,user="testuser"
        And there is a deployment with id=1,package_id=1,status='pending',user="testuser"

    @rest
    Scenario: omit required field
        When I query POST "/deployments?id=2"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                       |
            | query     |       | package_id is a required field.   |
        And there is no deployment with id=2

    @rest
    Scenario: attempt to set the status while posting
        When I query POST "/deployments?package_id=1&status=queued"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                   |
            | query     | status    | Status must be "pending" for new deployments. |
        And there is no deployment with package_id=1
        And there is no deployment with status="queued"

    @rest
    Scenario: attempt to violate a unique constraint
        Given there are deployments:
            | id    | user  | package_id    | status    |
            | 1     | foo   | 1             | pending   |
            | 2     | bar   | 2             | queued    |
        When I query POST "/deployments?package_id=1&id=1"
        Then the response code is 409
        And the response contains errors:
            | location  | name  | description                                                           |
            | query     | id    | Unique constraint violated. A deployment with this ID already exists. |
