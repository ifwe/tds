Feature: POST package(s) from the REST API by ID
    As a developer
    I want to add a new package
    So that the database has the proper information

    Background:
        Given I have a cookie with user permissions
        And there are applications:
            | name  |
            | app1  |
            | app2  |
            | app3  |
        And there is a package with version=1,revision=1

    @rest
    Scenario: add a new package
        When I query POST "/packages?name=app3&version=2&revision=2"
        Then the response code is 201
        And the response is an object with version="2",revision="2",creator="testuser"
        And there is a package with version="2",revision="2",creator="testuser"

    @rest
    Scenario: omit required field
        When I query POST "/packages?version=2&revision=2"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                   |
            | query     |       | name is a required field. |
        And there is no package with version="2",revision="2",creator="testuser"

    @rest
    Scenario: pass an name for an application that doesn't exist
        When I query POST "/packages?name=noexist&version=2&revision=2"
        Then the response code is 400
        And the response contains errors:
            | location  | name      | description                                   |
            | query     | name  | Application with name noexist does not exist. |
        And there is no package with version="2",revision="2",creator="testuser"

    @rest
    Scenario: pass an invalid parameter
        When I query POST "/packages?name=app3&version=2&revision=2&foo=bar"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                                                                       |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['status', 'name', 'builder', 'job', 'version', 'id', 'revision'].  |
        And there is no package with version="2",revision="2",creator="testuser"

    @rest
    Scenario Outline: attempt to violate a unique constraint
        When I query POST "/packages?name=app3&<query>"
        Then the response code is 409
        And the response contains errors:
            | location  | name      | description                                                   |
            | query     | <name>    | Unique constraint violated. A package <type> already exists.  |

        Examples:
            | query                     | name      | type                                                  |
            | version=1&revision=1&id=3 | version   | for this application with this version and revision   |
            | version=1&revision=1&id=3 | version   | for this application with this version and revision   |
            | version=1&revision=1&id=1 | id        | with this ID                                          |

    @rest
    Scenario Outline: attempt to set status to something other than pending
        When I query POST "/packages?name=app3&version=2&revision=2&status=<status>"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                               |
            | query     | status    | Status must be pending for new packages.  |
        And there is no package with version="2",revision="2",creator="testuser"

        Examples:
            | status        |
            | processing    |
            | failed        |
            | completed     |
            | removed       |
