Feature: OPTIONS for environments
    As a user
    I want to know my options for the environments endpoints
    So that I can avoid errors and be more effective in using the API

    @rest
    Scenario: get options for the collection endpoint
        When I query OPTIONS "/environments"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, OPTIONS, POST"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Get a list of environments, optionally by limit and/or start."
        And the response body contains "Add a new environment."
        And the response body contains "permissions"
        And the response body contains "admin"
        And the response body contains "name"
        And the response body contains "id"
        And the response body contains "short_name"
        And the response body contains "Unique string identifier"
        And the response body contains "Unique integer identifier"

    @rest
    Scenario: get options for the individual endpoint
        When I query OPTIONS "/environments/foo"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, OPTIONS, PUT"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Get environment matching name or ID."
        And the response body contains "Update environment matching name or ID."
        And the response body contains "Unique integer identifier"
        And the response body contains "permissions"
        And the response body contains "none"
        And the response body contains "admin"
        And the response body contains "Unique string identifier"
