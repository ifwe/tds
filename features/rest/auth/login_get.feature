Feature: Login GET method not allowed
    As a developer
    I want to get the appropriate error message when trying to GET /login
    So that I can have an easy interaction with the API

    @rest
    Scenario: try to GET /login
        When I query GET "/login"
        Then the response code is 405
        And the response contains errors:
            | location  | name      | description           |
            | url       | method    | Method not allowed.   |

    @rest
    Scenario: try to GET /login with parameters
        When I query GET "/login?user=foo&password=bar"
        Then the response code is 405
        And the response contains errors:
            | location  | name      | description           |
            | url       | method    | Method not allowed.   |
