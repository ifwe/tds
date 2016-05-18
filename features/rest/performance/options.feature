Feature: REST API performance OPTIONS
    As a developer
    I want to know my param options for the performance endpoint
    So that I can avoid errors in my queries

    @rest
    Scenario: get options for the performance endpoint
        When I query OPTIONS "/performance"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, HEAD, OPTIONS"
        And the response body contains "Get metrics packages, tier deployments, host deployments, and deployments by month for all months."
        And the response body contains "Do a GET query without a body returned."
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
