Feature: OPTIONS for packages
    As a user
    I want to know my options for the packages endpoints
    So that I can avoid errors and be more effective in using the API

    @rest
    Scenario: get options for the collection endpoint
        When I query OPTIONS "/applications/foo/packages"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, HEAD, OPTIONS, POST"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Get a list of packages for an application, optionally by limit and/or start."
        And the response body contains "Add a new package for an application."
        And the response body contains "Do a GET query without a body returned."
        And the response body contains "permissions"
        And the response body contains "user"
        And the response body contains "id"
        And the response body contains "version"
        And the response body contains "revision"
        And the response body contains "application_id"
        And the response body contains "Unique integer identifier"
        And the response body contains "required"

    @rest
    Scenario: get options for the individual endpoint
        When I query OPTIONS "/applications/foo/packages/bar/biz"
        Then the response code is 200
        And the response header contains "Allows" set to "GET, HEAD, OPTIONS, PUT"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "Get package for an application with version and revision."
        And the response body contains "Update package for an application with version and revision."
        And the response body contains "Do a GET query without a body returned."
        And the response body contains "permissions"
        And the response body contains "user"
        And the response body contains "Unique integer identifier"
        And the response body contains "id"
        And the response body contains "version"
        And the response body contains "revision"
        And the response body contains "application_id"
