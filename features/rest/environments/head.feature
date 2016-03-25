Feature: HEAD environment(s) from the REST API
    As a user
    I want to test my GET query
    So that I can be sure my query is not malformed

    Background:
        Given I have a cookie with user permissions
        And there is an environment with name="dev"
        And there is an environment with name="staging"

    @rest
    Scenario Outline: get an environment that doesn't exist
        When I query HEAD "/environments/<select>"
        Then the response code is 404
        And the response body is empty

        Examples:
            | select    |
            | noexist   |
            | 500       |

    @rest
    Scenario: get all environments
        When I query HEAD "/environments"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario Outline: get a single environment
        When I query HEAD "/environments/<select>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | select        |
            | 1             |
            | development   |
