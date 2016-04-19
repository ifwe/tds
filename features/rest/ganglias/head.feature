Feature: HEAD Ganglia(s) from the REST API
    As a user
    I want to test my GET query
    So that I can be sure my query is not malformed

    Background:
        Given I have a cookie with user permissions
        And there is a Ganglia with cluster_name="ganglia1"
        And there is a Ganglia with cluster_name="ganglia2"

    @rest
    Scenario Outline: get a Ganglia that doesn't exist
        When I query HEAD "/ganglias/<select>"
        Then the response code is 404
        And the response body is empty

        Examples:
            | select    |
            | noexist   |
            | 500       |

    @rest
    Scenario: get all Ganglias
        When I query HEAD "/ganglias"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario Outline: get a single Ganglia
        When I query HEAD "/ganglias/<select>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | select    |
            | ganglia1  |
            | 2         |

    @rest
    Scenario Outline: specify limit and/or last queries
        Given there is a Ganglia with cluster_name="ganglia3"
        And there is a Ganglia with cluster_name="ganglia4"
        When I query HEAD "/ganglias?limit=<limit>&start=<start>"
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
        When I query HEAD "/ganglias?<query>"
        Then the response code is 422
        And the response body is empty

        Examples:
            | query             |
            | foo=bar           |
            | limit=10&foo=bar  |
            | foo=bar&start=2   |
