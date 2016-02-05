Feature: Login
    As a developer
    I want to login
    So that I can have access to interact with the REST API

    @rest
    Scenario Outline: insufficient parameters
        When I POST "{<body>}" to "/login"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                                                                                               |
            | body      |       | Could not parse body as valid JSON. Body must be a JSON object with attributes "username" and "password". |

        Examples:
            | body              |
            |                   |
            | "password": "bar" |
            | "username": "foo" |

    @rest
    Scenario: invalid credentials
        When I POST "{"username": "horsefeathers", "password": "hensteeth"}" to "/login"
        Then the response code is 401
        And the response does not contain a cookie
        And the response contains errors:
            | location  | name      | description                                                                   |
            | query     | user      | Authentication failed. Please check your username and password and try again. |

    @rest @ldap_off
    Scenario: LDAP server not accessible
        When I POST "{"username": "horsefeathers", "password": "hensteeth"}" to "/login"
        Then the response code is 500
        And the response contains errors:
            | location  | name  | description                       |
            | url       |       | Could not connect to LDAP server. |

    @rest
    Scenario: valid credentials
        When I POST "{"username": "testuser", "password": "secret"}" to "/login"
        Then the response code is 200
        And the response contains a cookie
