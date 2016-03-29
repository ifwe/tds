Feature: OPTIONS for Ganglias
    As a user
    I want to know my options for the Ganglias endpoints
    So that I can avoid errors and be more effective in using the API

    @rest
    Scenario: get options for the collection endpoint
        When I query OPTIONS "/ganglias"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, HEAD, OPTIONS, POST"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Get a list of Ganglias, optionally by limit and/or start."
        And the response body contains "Add a new Ganglia."
        And the response body contains "Do a GET query without a body returned."
        And the response body contains "permissions"
        And the response body contains "admin"
        And the response body contains "user"
        And the response body contains "id"
        And the response body contains "name"
        And the response body contains "Unique integer identifier"
        And the response body contains "Unique string identifier"
        And the response body contains "required"

    @rest
    Scenario: get options for the individual endpoint
        When I query OPTIONS "/ganglias/foo"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, HEAD, OPTIONS, PUT"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Get Ganglia matching name or ID."
        And the response body contains "Update Ganglia matching name or ID."
        And the response body contains "Do a GET query without a body returned."
        And the response body contains "permissions"
        And the response body contains "admin"
        And the response body contains "user"
        And the response body contains "Unique integer identifier"
        And the response body contains "Unique string identifier"
        And the response body contains "id"
        And the response body contains "name"
