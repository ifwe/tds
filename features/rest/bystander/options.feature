Feature: REST API bystander OPTIONS
    As a developer
    I want to know my param options for the bystander endpoint
    So that I can avoid errors in my queries

    @rest
    Scenario: get options for the bystander endpoint
        When I query OPTIONS "/bystander"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, HEAD, OPTIONS"
        And the response body contains "Get latest deployed version of all applications on all associated tiers in each environment."
        And the response body contains "Do a GET query without a body returned."
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
