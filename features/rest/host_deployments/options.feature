Feature: OPTIONS for host deployments
    As a user
    I want to know my options for the host deployments endpoints
    So that I can avoid errors and be more effective in using the API

    @rest
    Scenario: get options for the collection endpoint
        When I query OPTIONS "/host_deployments"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, HEAD, OPTIONS, POST"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Get a list of host deployments, optionally by limit and/or start."
        And the response body contains "Add a new host deployment."
        And the response body contains "Do a GET query without a body returned."
        And the response body contains "permissions"
        And the response body contains "user"
        And the response body contains "id"
        And the response body contains "host_id"
        And the response body contains "deployment_id"
        And the response body contains "Unique integer identifier"
        And the response body contains "unique_together"
        And the response body contains "required"
        And the response body contains "returns"

    @rest
    Scenario: get options for the individual endpoint
        When I query OPTIONS "/host_deployments/foo"
        Then the response code is 200
        And the response header contains "Allows" set to "DELETE, GET, HEAD, OPTIONS, PUT"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Get host deployment matching ID."
        And the response body contains "Update host deployment matching ID."
        And the response body contains "Delete host deployment matching ID."
        And the response body contains "Do a GET query without a body returned."
        And the response body contains "permissions"
        And the response body contains "user"
        And the response body contains "Unique integer identifier"
        And the response body contains "unique_together"
        And the response body contains "id"
        And the response body contains "host_id"
        And the response body contains "deployment_id"
        And the response body contains "returns"
