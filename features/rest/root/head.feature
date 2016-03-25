Feature: REST API root HEAD
    As a developer
    I want to test my GET query
    So that I can be sure my query is not malformed

    @rest
    Scenario: get all URLs
        When I query HEAD on the root url
        Then the response code is 200
        And the response body is empty
