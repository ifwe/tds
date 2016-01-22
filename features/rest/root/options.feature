Feature: REST API root OPTIONS
    As a developer
    I want to know my param options for the root URL endpoint
    So that I can use the root URL endpoing more effectively

    @rest
    Scenario: get options for root URL
        When I query OPTIONS "/"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, OPTIONS"
        And the response body contains "Get all supported URLS."
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "description"
        And the response body contains "GET"
        And the response body contains "OPTIONS"
