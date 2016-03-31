Feature: OPTIONS for application-tier associations
    As a user
    I want to know what my options are for the application-tier endpoints
    So that I can avoid errors and be more effective in using the API

    @rest
    Scenario: get options for the collection endpoint
        When I query OPTIONS "/projects/foo/applications/bar/tiers"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, HEAD, OPTIONS, POST"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Get all project-application-tier associations."
        And the response body contains "Create new association for project-application of tier with given ID or name (ID given precedence)."
        And the response body contains "Do a GET query without a body returned."
        And the response body contains "id"
        And the response body contains "name"
        And the response body contains "Unique integer identifier for the project"
        And the response body contains "Unique integer identifier for the application"
        And the response body contains "Unique integer identifier for the tier"
        And the response body contains "returns"
        And the response body contains "Newly created project-application-tier association"

    @rest
    Scenario: get options for the individual endpoint
        When I query OPTIONS "/projects/foo/applications/bar/tiers/biz"
        Then the response code is 200
        And the response header contains "Allows" set to "DELETE, GET, HEAD, OPTIONS"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Get project-application-tier association."
        And the response body contains "Delete project-application-tier association."
        And the response body contains "Do a GET query without a body returned."
        And the response body contains "application_id"
        And the response body contains "project_id"
        And the response body contains "tier_id"
        And the response body contains "Unique integer identifier for the project"
        And the response body contains "Unique integer identifier for the application"
        And the response body contains "Unique integer identifier for the tier"
        And the response body contains "returns"
        And the response body contains "Deleted project-application-tier association"
