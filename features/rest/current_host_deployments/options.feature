Feature: OPTIONS for most recent host deployment
    As a user
    I want to know my options for the most recent completed host deployment endpoint
    So that I can avoid errors and be more effective in using the API

    @rest
    Scenario: get options for the endpoint
        When I query OPTIONS "/applications/foo/hosts/bar"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, OPTIONS"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Get the most recent completed host deployment for an application and host."
        And the response body contains "id"
        And the response body contains "deployment_id"
        And the response body contains "package_id"
        And the response body contains "host_id"
        And the response body contains "Unique integer identifier"
