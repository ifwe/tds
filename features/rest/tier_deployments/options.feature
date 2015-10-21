Feature: OPTIONS for tier deployments
    As a user
    I want to know my options for the tier deployments endpoints
    So that I can avoid errors and be more effective in using the API

    @rest
    Scenario: get options for the collection endpoint
        When I query OPTIONS "/tier_deployments"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, OPTIONS, POST"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Get a list of tier deployments, optionally by limit and/or start."
        And the response body contains "Add a new tier deployment."
        And the response body contains "permissions"
        And the response body contains "user"
        And the response body contains "id"
        And the response body contains "tier_id"
        And the response body contains "deployment_id"
        And the response body contains "environment_id"
        And the response body contains "Unique integer identifier"
        And the response body contains "unique_together"
        And the response body contains "required"

    @rest
    Scenario: get options for the individual endpoint
        When I query OPTIONS "/tier_deployments/foo"
        Then the response code is 200
        And the response header contains "Allows" set to "DELETE, GET, OPTIONS, PUT"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Get tier deployment matching ID."
        And the response body contains "Update tier deployment matching ID."
        And the response body contains "Delete tier deployment matching ID."
        And the response body contains "permissions"
        And the response body contains "user"
        And the response body contains "Unique integer identifier"
        And the response body contains "unique_together"
        And the response body contains "id"
        And the response body contains "tier_id"
        And the response body contains "deployment_id"
        And the response body contains "environment_id"
