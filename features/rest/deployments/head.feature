Feature: HEAD deployment(s) from the REST API
    As a developer
    I want to test my GET query
    So that I can be sure my query is not malformed

    Background:
        Given I have a cookie with user permissions

    @rest
    Scenario: no deployments
        When I query HEAD "/deployments"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario: get a deployment that doesn't exist
        When I query HEAD "/deployments/500"
        Then the response code is 404
        And the response body is empty

    @rest
    Scenario: get all deployments
        Given there are deployments:
            | id    | user  | status        | duration  |
            | 1     | foo   | pending       | 1         |
            | 2     | bar   | queued        | 0         |
            | 3     | baz   | inprogress    | 20        |
        When I query HEAD "/deployments"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario: get a specific deployment
        Given there are deployments:
            | id    | user  | status        | duration  |
            | 1     | foo   | pending       | 1         |
            | 2     | bar   | queued        | 0         |
            | 3     | baz   | inprogress    | 20        |
        When I query HEAD "/deployments/2"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario Outline: specify limit and/or last queries
        Given there are deployments:
            | id    | user  | status        |
            | 1     | foo   | pending       |
            | 2     | bar   | queued        |
            | 3     | baz   | inprogress    |
            | 4     | bar   | queued        |
            | 5     | baz   | inprogress    |
        When I query HEAD "/deployments?limit=<limit>&start=<start>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | limit | start |
            |       |       |
            |       | 1     |
            | 10    |       |
            | 4     | 1     |
            |       |       |
            |       | 2     |
