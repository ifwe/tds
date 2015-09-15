Feature: Update (PUT) package on REST API by ID
    As a developer
    I want to update information for a package
    So that the database has the proper information

    Background:
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
        And there are packages:
            | version   | revision  |
            | 1         | 2         |
            | 2         | 1         |
            | 2         | 2         |
            | 2         | 3         |
            | 3         | 1         |
        And I have a cookie with user permissions

    @rest
    Scenario: update a package that doesn't exist
        When I query PUT "/packages/500?version=500"
        Then the response code is 404
        And the response contains errors:
            | location  | name  | description                           |
            | path      | id    | Package with ID 500 does not exist.   |
        And there is no package with version="500"

    @rest
    Scenario: pass an invalid parameter
        When I query PUT "/packages/1?foo=bar&version=500"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                                                                       |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['status', 'name', 'builder', 'job', 'version', 'id', 'revision'].  |
        And there is no package with version="500"

    @rest
    Scenario Outline: update a package
        When I query PUT "/packages/1?<query>"
        Then the response code is 200
        And the response is an object with <params>
        And there is a package with <props>

        Examples:
            | query     | params        | props             |
            | name=app1 | name="app1"   | pkg_name="app1"   |

    @rest
    Scenario Outline: attempt to violate a unique constraint
        Given there is an application with name="app3"
        And there are packages:
            | version   | revision  |
            | 2         | 2         |
            | 2         | 3         |
        When I query PUT "/packages/4?revision=2&<query>"
        Then the response code is 409
        And the response contains errors:
            | location  | name      | description                                                                                                       |
            | query     | <name>    | Unique constraint violated. Another package for this application with this version and revision already exists.   |
        And there is a package with version=2,revision=3,pkg_name="app2"

        Examples:
            | query                 | name          |
            |                       | revision      |
            | version=2             | version       |
            | name=app3&version=2   | name          |

    @rest
    Scenario Outline: attempt to set status to pending from something other than failed
        Given there are packages:
            | version   | revision  | status    |
            | 3         | 2         | <status>  |
        When I query PUT "/packages/6?status=pending"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                       |
            | query     | status    | Cannot change status to pending from <status>.    |
        And there is no package with version=3,revision=2,status="pending"
        And there is a package with version=3,revision=2,status="<status>"

        Examples:
            | status        |
            | processing    |
            | completed     |
            | removed       |

    @rest
    Scenario: change status back to pending from failed
        Given there are packages:
            | version   | revision  | status    |
            | 3         | 2         | failed    |
        When I query PUT "/packages/6?status=pending"
        Then the response code is 200
        And the response is an object with version="3",revision="2",status="pending"
        And there is no package with version=3,revision=2,status="failed"
        And there is a package with version=3,revision=2,status="pending"
