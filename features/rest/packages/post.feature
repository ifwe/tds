Feature: Add (POST) package on REST API
    As a developer
    I want to add a new package
    So that the database has the proper information

    Background:
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
            | app3  |
        And there is a package with version=1,revision=1
        And I have a cookie with user permissions

    @rest
    Scenario Outline: add a new package
        When I query POST "/applications/<select>/packages?version=<ver>&revision=<rev>"
        Then the response code is 201
        And the response is an object with version="<ver>",revision="<rev>",creator="testuser"
        And there is a package with version="<ver>",revision="<rev>",creator="testuser"

        Examples:
            | select    | ver   | rev   |
            | app3      | 2     | 2     |
            | 4         | 2     | 2     |

    @rest
    Scenario: specify id
        When I query POST "/applications/app3/packages?version=2&revision=2&id=10"
        Then the response code is 201
        And the response is an object with version="2",revision="2",id=10
        And there is a package with version="2",revision="2",id=10

    @rest
    Scenario: omit required field
        When I query POST "/applications/app3/packages?revision=2"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                   |
            | query     |       | version is a required field.  |
        And there is no package with version="2",revision="2"

    @rest
    Scenario Outline: pass an invalid parameter
        When I query POST "/applications/app3/packages?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                                                           |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['status', 'builder', 'job', 'version', 'id', 'revision'].  |
        And there is no package with version="2",revision="2"

        Examples:
            | query                         |
            | version=2&revision=2&foo=bar  |
            | foo=bar&version=2&revision=2  |

    @rest
    Scenario Outline: attempt to violate a unique constraint
        When I query POST "/applications/app3/packages?<query>"
        Then the response code is 409
        And the response contains errors:
            | location  | name      | description                                                   |
            | query     | <name>    | Unique constraint violated. A package <type> already exists.  |

        Examples:
            | query                     | name      | type                                                  |
            | version=1&revision=1      | version   | for this application with this version and revision   |
            | version=1&revision=1&id=3 | version   | for this application with this version and revision   |
            | version=2&revision=2&id=1 | id        | with this ID                                          |
