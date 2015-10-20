Feature: OPTIONS for login
    As a user
    I want to know what my options are for the login endpoint
    So that I can login without errors

    Background:
        Given I have a cookie with user permissions

    @rest
    Scenario: get options for the login endpoint
        When I query OPTIONS "/login"
        Then the response code is 200
        And the response header contains "Allows" set to "OPTIONS, POST"
        And the response body contains "Get HTTP method options and parameters for this URL endpoint."
        And the response body contains "description"
        And the response body contains "Authenticate and get a session cookie."
        And the response body contains "returns"
        And the response body contains "Session cookie attached at cookies->session."
        And the response body contains "user"
        And the response body contains "string"
        And the response body contains "LDAP username to use for authentication"
        And the response body contains "password"
        And the response body contains "String password to use for authentication"
        And the response body contains "required"
