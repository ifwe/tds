Feature: GET package(s) from the REST API by ID
    As a developer
    I want information packages
    So that I can be informed of the current status of the database

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
    Scenario: get all packages
        When I query GET "/packages"
        Then the response code is 200
        And the response is a list of 5 items
        And the response list contains objects:
            | version   | revision  |
            | 1         | 2         |
            | 2         | 1         |
            | 2         | 2         |
            | 2         | 3         |
            | 3         | 1         |
        And the response list objects do not contain attributes creator,pkg_def_id,pkg_name

    @rest
    Scenario: get all packages with select query
        When I query GET "/packages?select=version,revision"
        Then the response code is 200
        And the response is a list of 5 items
        And the response list contains objects:
            | version   | revision  |
            | 1         | 2         |
            | 2         | 1         |
            | 2         | 2         |
            | 2         | 3         |
            | 3         | 1         |
        And the response list objects do not contain attributes id,status,builder,user,job,name,creator,pkg_def_id,pkg_name

    @rest
    Scenario: get a package by ID
        When I query GET "/packages/2"
        Then the response code is 200
        And the response is an object with version="2",revision="1"
        And the response object does not contain attributes creator,pkg_def_id,pkg_name

    @rest
    Scenario: get a package by ID with select query
        When I query GET "/packages/2?select=version,revision"
        Then the response code is 200
        And the response is an object with version="2",revision="1"
        And the response object does not contain attributes id,status,builder,user,job,name,creator,pkg_def_id,pkg_name

    @rest
    Scenario: get a package that doesn't exist
        When I query GET "/packages/500"
        Then the response code is 404
        And the response contains errors:
            | location  | name  | description                           |
            | path      | id    | Package with ID 500 does not exist.   |

    @rest
    Scenario: specify unknown query
        When I query GET "/packages?foo=bar"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                               |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['limit', 'select', 'start'].   |

    @rest
    Scenario Outline: specify limit and/or last queries
        When I query GET "/packages?limit=<limit>&start=<start>"
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
            | 10    |       | 5     | 1     | 5     |
            | 4     | 1     | 4     | 1     | 4     |
