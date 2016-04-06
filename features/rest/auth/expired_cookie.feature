Feature: Expired cookie detection
    As an API developer
    I want to prevent users from gaining access with expired cookies
    So that the API can be secure

    @rest
    Scenario: attempt to use an expired cookie
        Given I have a cookie with user permissions
        And I change cookie life to 1
        And I wait 3 seconds
        When I query GET "/projects"
        Then the response code is 419
        And the response contains errors:
            | location  | name      | description                                               |
            | header    | cookie    | Cookie has expired or is invalid. Please reauthenticate.  |

    @rest
    Scenario: use an eternal cookie to get access after cookie life
        Given "testuser" is an eternal user in the REST API
        And I have a cookie with user permissions and eternal=True
        And I change cookie life to 1
        And I wait 3 seconds
        When I query GET "/projects"
        Then the response code is 200
