Feature: GET deployment(s) from the REST API
    As a developer
    I want information on deployments
    So that I can be informed of the current state of the database

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
    Scenario: no deployments
        When I query GET "/deployments"
        Then the response code is 200
        And the response is a list of 0 items

    @rest
    Scenario: get a deployment that doesn't exist
        When I query GET "/deployments/500"
        Then the response code is 404
        And the response contains errors:
            | location  | name  | description                               |
            | path      | id    | Deployment with ID 500 does not exist.    |

    @rest
    Scenario: get all deployments
        Given there are deployments:
            | id    | user  | package_id    | status        |
            | 1     | foo   | 1             | pending       |
            | 2     | bar   | 2             | queued        |
            | 3     | baz   | 3             | inprogress    |
        When I query GET "/deployments"
        Then the response code is 200
        And the response is a list of 3 items
        And the response list contains an object with id=1,user="foo",package_id=1,status="pending"
        And the response list contains an object with id=2,user="bar",package_id=2,status="queued"
        And the response list contains an object with id=3,user="baz",package_id=3,status="inprogress"

    @rest
    Scenario: get a specific deployment
        Given there are deployments:
            | id    | user  | package_id    | status        |
            | 1     | foo   | 1             | pending       |
            | 2     | bar   | 2             | queued        |
            | 3     | baz   | 3             | inprogress    |
        When I query GET "/deployments/2"
        Then the response code is 200
        And the response is an object with id=2,user="bar",package_id=2,status="queued"

    @rest
    Scenario Outline: specify limit and/or last queries
        Given there are deployments:
            | id    | user  | package_id    | status        |
            | 1     | foo   | 1             | pending       |
            | 2     | bar   | 2             | queued        |
            | 3     | baz   | 3             | inprogress    |
            | 4     | bar   | 2             | queued        |
            | 5     | baz   | 3             | inprogress    |
        When I query GET "/deployments?limit=<limit>&start=<start>"
        Then the response code is 200
        And the response is a list of <num> items
        And the response list contains id range <min> to <max>

        Examples:
            | limit | start | num   | min   | max   |
            |       |       | 5     | 1     | 5     |
            |       | 1     | 5     | 1     | 5     |
            | 10    |       | 5     | 1     | 5     |
            | 4     | 1     | 4     | 1     | 4     |
            |       |       | 5     | 1     | 5     |
            |       | 2     | 4     | 2     | 5     |
