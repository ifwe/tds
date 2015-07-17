Feature: Update (PUT) application on REST API
    As a developer
    I want to update information for one of my applications
    So that the database has the proper information

    Background:
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
            | app3  |
        And I have a cookie with user permissions

    @rest
    Scenario Outline: update an application that doesn't exist
        When I query PUT "/applications/<select>?name=newname"
        Then the response code is 404
        And the response contains errors:
            | location  | name          | description                                   |
            | path      | name_or_id    | Application with <descript> does not exist.   |

        Examples:
            | select    | descript      |
            | noexist   | name noexist  |
            | 500       | ID 500        |

    @rest
    Scenario Outline: update an application
        When I query PUT "/applications/<select>?name=newname"
        Then the response code is 200
        And the response is an object with pkg_name="newname",id=2
        And there is an application with pkg_name="newname",id=2

        Examples:
            | select    |
            | app1      |
            | 2         |

    @rest
    Scenario Outline: pass an invalid parameter
        When I query PUT "/applications/<select>?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                                                                                                              |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['job', 'validation_type', 'env_specific', 'name', 'build_host', 'deploy_type', 'arch', 'id', 'build_type'].   |
        And there is an application with pkg_name="app1",id=2

        Examples:
            | select    | query                     |
            | app1      | foo=bar                   |
            | 2         | foo=bar                   |
            | app1      | pkg_name=newname&foo=bar  |
            | 2         | pkg_name=newname&foo=bar  |
            | app1      | foo=bar&pkg_name=newname  |
            | 2         | foo=bar&pkg_name=newname  |

    @rest
    Scenario Outline: attempt to violate a unique constraint
        When I query PUT "/applications/<select>?<query>"
        Then the response code is 409
        And the response contains errors:
            | location  | name      | description                                                                        |
            | query     | <name>    | Unique constraint violated. Another application with this <type> already exists.   |
        And there is an application with pkg_name="app1",id=2

        Examples:
            | select    | query             | name  | type  |
            | app1      | name=app2         | name  | name  |
            | 2         | name=app2         | name  | name  |
            | app1      | id=3              | id    | ID    |
            | 2         | id=3              | id    | ID    |
            | app1      | name=app2&id=3    | name  | name  |
            | app1      | name=app2&id=3    | id    | ID    |
            | 2         | name=app2&id=3    | name  | name  |
            | 2         | name=app2&id=3    | id    | ID    |
