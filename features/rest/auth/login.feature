Feature: Login
    As a developer
    I want to login
    So that I can have access to interact with the REST API

    @rest
    Scenario Outline: insufficient parameters
        When I query POST "/login?<params>"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                   |
            | query     |       | <name> is a required field.   |

        Examples:
            | params                | name      |
            |                       | user      |
            |                       | password  |
            | password=bar          | user      |
            | user=foo              | password  |
            | user=&password=bar    | user      |
            | user=foo&password=    | password  |
            | user=&password=       | user      |
            | user=&password=       | password  |

    @rest
    Scenario: invalid credentials
        When I query POST "/login?user=horsefeathers&password=hensteeth"
        Then the response code is 401
        And the response does not contain a cookie
        And the response contains errors:
            | location  | name      | description                                                                   |
            | query     | user      | Authentication failed. Please check your username and password and try again. |

    @rest @ldap_off
    Scenario: LDAP server not accessible
        When I query POST "/login?user=horsefeathers&password=hensteeth"
        Then the response code is 500
        And the response contains errors:
            | location  | name  | description                       |
            | url       |       | Could not connect to LDAP server. |

    @rest
    Scenario: valid credentials
        When I query POST "/login?user=testuser&password=secret"
        Then the response code is 200
        And the response contains a cookie
