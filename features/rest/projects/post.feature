Feature: Add (POST) project on REST API
    As a developer
    I want to add a new project
    So that the database has the proper information

    Background:
        Given there are projects:
            | name  |
            | proj1 |
            | proj2 |
            | proj3 |

    @rest
    Scenario: add a new project
        When I query POST "/projects?name=proj4"
        Then the response code is 201
        And the response is an object with name="proj4",id=4
        And there is a project with name="proj4",id=4

    @rest
    Scenario: specify id
        When I query POST "/projects?name=proj4&id=10"
        Then the response code is 201
        And the response is an object with name="proj4",id=10
        And there is a project with name="proj4",id=10

    @rest
    Scenario: omit required field
        When I query POST "/projects"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description               |
            | query     |       | name is a required field. |
        And there is no project with name="proj4"

    @rest
    Scenario Outline: pass an invalid parameter
        When I query POST "/projects?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                               |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['id', 'name']. |
        And there is no project with name="proj4"

        Examples:
            | query                |
            | name=proj4&foo=bar   |
            | foo=bar&name=proj4   |

    @rest
    Scenario Outline: attempt to violate a unique constraint
        When I query POST "/projects?<query>"
        Then the response code is 409
        And the response contains errors:
            | location  | name      | description                                                               |
            | query     | <name>    | Unique constraint violated. A project with this <type> already exists.    |

        Examples:
            | query             | name  | type  |
            | name=proj3        | name  | name  |
            | name=proj3&id=2   | name  | name  |
            | name=proj3&id=2   | id    | ID    |
