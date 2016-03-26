Feature: HEAD project(s) from the REST API
    As a developer
    I want to test my GET query
    So that I can be sure my query is not malformed

    Background:
        Given I have a cookie with user permissions

    @rest
    Scenario: no projects
        When I query HEAD "/projects"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario Outline: get a project that doesn't exist
        When I query HEAD "/projects/<select>"
        Then the response code is 404
        And the response body is empty

        Examples:
            | select    |
            | noexist   |
            | 5         |

    @rest
    Scenario: get all projects
        Given there are projects:
            | name  |
            | proj1 |
            | proj2 |
            | proj3 |
        When I query HEAD "/projects"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario Outline: get a single project by name
        Given there are projects:
            | name  |
            | proj1 |
            | proj2 |
            | proj3 |
        When I query HEAD "/projects/<proj>"
        Then the response code is 200
        And the response body is empty

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
        When I query HEAD "/projects/<id>"
        Then the response code is 200
        And the response body is empty

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
        When I query HEAD "/projects?limit=<limit>&start=<start>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | limit | start |
            |       |       |
            |       | 2     |
            | 10    |       |
            | 4     | 1     |

    @rest
    Scenario Outline: specify unknown query
        Given there are projects:
            | name  |
            | proj1 |
            | proj2 |
            | proj3 |
            | proj4 |
            | proj5 |
        When I query HEAD "/projects?<query>"
        Then the response code is 422
        And the response body is empty

        Examples:
            | query             |
            | foo=bar           |
            | limit=10&foo=bar  |
            | foo=bar&start=2   |
