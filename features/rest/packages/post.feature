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

    @rest @wip
    Scenario Outline: add a new package
        When I query POST "/applications/<select>/packages?version=<ver>&revision=<rev>"
        Then the response code is 201
        And the response is an object with version=<ver>,revision=<rev>
        And there is a package with version=<ver>,revision=<rev>

        Examples:
            | select    | ver   | rev   |
            | app3      | 2     | 2     |
            | 4         | 2     | 2     |

    @rest
    Scenario: specify id
        When I query POST "/packages?name=pkg4&id=10"
        Then the response code is 201
        And the response is an object with name="pkg4",id=10
        And there is a package with name="pkg4",id=10

    @rest
    Scenario: omit required field
        When I query POST "/packages"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description               |
            | query     |       | name is a required field. |
        And there is no package with name="pkg4"

    @rest
    Scenario Outline: pass an invalid parameter
        When I query POST "/packages?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                               |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['id', 'name']. |
        And there is no package with name="pkg4"

        Examples:
            | query                |
            | name=pkg4&foo=bar   |
            | foo=bar&name=pkg4   |

    @rest
    Scenario Outline: attempt to violate a unique constraint
        When I query POST "/packages?<query>"
        Then the response code is 409
        And the response contains errors:
            | location  | name      | description                                                               |
            | query     | <name>    | Unique constraint violated. A package with this <type> already exists.    |

        Examples:
            | query             | name  | type  |
            | name=pkg3        | name  | name  |
            | name=pkg3&id=2   | name  | name  |
            | name=pkg3&id=2   | id    | ID    |
