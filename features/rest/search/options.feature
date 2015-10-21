Feature: REST API search OPTIONS
    As a developer
    I want to know my param options for the search endpoint
    So that I can avoid errors in my queries

    @rest
    Scenario: get options for search tiers
        When I query OPTIONS "/search/tiers"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, OPTIONS"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "description"
        And the response body contains "type"
        And the response body contains "Unique integer identifier"
        And the response body contains "GET"
        And the response body contains "OPTIONS"
        And the response body does not contain "POST"
        And the response body does not contain "PUT"
        And the response body does not contain "DELETE"
