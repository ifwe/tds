Feature: OPTIONS for most recent tier deployment
    As a user
    I want to know my options for the most recent tier deployment endpoint
    So that I can avoid errors and be more effective in using the API

    @rest
    Scenario: get options for the endpoint
        When I query OPTIONS "/applications/foo/tiers/bar/environments/biz"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, HEAD, OPTIONS"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Get the most recent completed tier deployment for an application, tier, and environment."
        And the response body contains "Do a GET query without a body returned."
        And the response body contains "id"
        And the response body contains "deployment_id"
        And the response body contains "package_id"
        And the response body contains "tier_id"
        And the response body contains "Unique integer identifier"
