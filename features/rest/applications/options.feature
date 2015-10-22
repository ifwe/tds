Feature: OPTIONS for applications
    As a user
    I want to know what my options are for applications endpoints
    So that I can avoid errors and be more effective in using the API

    @rest
    Scenario: get options for the collection endpoint
        When I query OPTIONS "/applications"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, OPTIONS, POST"
        And the response body contains "Get HTTP method options and parameters"
        And the response body contains "Unique integer identifier"
        And the response body contains "type"
        And the response body contains "description"
        And the response body contains "required"
        And the response body contains "limit"
        And the response body contains "start"
        And the response body contains "id"
        And the response body contains "name"

    @rest
    Scenario: get options for the individual endpoint
        When I query OPTIONS "/applications/foo"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, OPTIONS, PUT"
        And the response body contains "Get HTTP method options and parameters"
        And the response body contains "Update application matching name or ID."
        And the response body contains "Get application matching name or ID."
        And the response body contains "type"
        And the response body contains "description"
        And the response body contains "id"
        And the response body contains "name"
