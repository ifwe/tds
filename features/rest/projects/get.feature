Feature: GET project(s) from the REST API
    As a developer
    I want information on projects
    So that I can be informed of the current state of the database

    @rest
    Scenario: no projects
        When I query GET "/projects"
        Then the response code is 200
        And the response is a list of 0 items

    @rest
    Scenario: get a project that doesn't exist
        When I query GET "/projects/noexist"
        Then the response code is 404

    @rest
    Scenario: get all projects
        Given there are projects:
            | name  |
            | proj1 |
            | proj2 |
            | proj3 |
        When I query GET "/projects"
        Then the response code is 200
        And the response is a list of 3 items
        And the response list contains objects:
            | name  |
            | proj1 |
            | proj2 |
            | proj3 |

    @rest
    Scenario Outline: get a single project by name
        Given there are projects:
            | name  |
            | proj1 |
            | proj2 |
            | proj3 |
        When I query GET "/projects/<proj>"
        Then the response code is 200
        And the response is an object with name="<proj>"

        Examples:
            | proj  |
            | proj1 |
            | proj2 |
            | proj3 |

    @rest
    Scenario Outline: get a single project by ID
        Given there are projects:
            | name  |
            | proj1 |
            | proj2 |
            | proj3 |
        When I query GET "/projects/<id>"
        Then the response code is 200
        And the response is an object with id=<id>

        Examples:
            | id    |
            | 1     |
            | 2     |
            | 3     |

    @rest
    Scenario Outline: specify limit and/or last queries
        Given there are projects:
            | name  |
            | proj1 |
            | proj2 |
            | proj3 |
            | proj4 |
            | proj5 |
        When I query GET "/projects?limit=<limit>&start=<start>"
        Then the response code is 200
        And the response is a list of <num> items
        And the response list contains id range <min> to <max>

        Examples:
            | limit | start | num   | min   | max   |
            |       |       | 5     | 1     | 5     |
            |       | 2     | 4     | 2     | 5     |
            | 10    |       | 5     | 1     | 5     |
            | 4     | 1     | 4     | 1     | 4     |

    @rest
    Scenario Outline: specify unknown query
        Given there are projects:
            | name  |
            | proj1 |
            | proj2 |
            | proj3 |
            | proj4 |
            | proj5 |
        When I query GET "/projects?<query>"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                                                   |
            | query     | foo   | Unsupported query: foo. Valid parameters: ('limit', 'start')  |

        Examples:
            | query             |
            | foo=bar           |
            | limit=10&foo=bar  |
            | foo=bar&last=2    |
