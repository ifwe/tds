Feature: Add (POST) application on REST API
    As a developer
    I want to add a new application
    So that the database has the proper information

    Background:
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
            | app3  |
        And I have a cookie with user permissions

    @rest
    Scenario: add a new application
        When I query POST "/applications?name=app4&job=myjob"
        Then the response code is 201
        And the response is an object with pkg_name="app4",id=5
        And there is an application with name="app4",id=5

    @rest
    Scenario Outline: specify advanced parameters
        When I query POST "/applications?name=app4&job=myjob&<query>"
        Then the response code is 201
        And the response is an object with pkg_name="app4",id=5,<props>
        And there is an application with name="app4",id=5,<props>

        Examples:
            | query                     | props                         |
            | build_host=ci.example.org | build_host="ci.example.org"   |
            | build_type=hudson         | build_type="hudson"           |
            | deploy_type=deb           | deploy_type="deb"             |
            | arch=x86_64               | arch="x86_64"                 |
            | validation_type=valtype   | validation_type="valtype"     |
            | env_specific=1            | env_specific=True             |

    @rest
    Scenario Outline: omit required fields
        When I query POST "/applications?<query>"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                   |
            | query     |       | <field> is a required field.  |
        And there is no application with pkg_name="app4"
        And there is no application with path="myjob"

        Examples:
            | query                     | field |
            | name=app4                 | job   |
            | job=myjob                 | name  |
            | foo=bar&name=app4         | job   |
            | foo=bar&job=myjob         | name  |

    @rest
    Scenario Outline: pass an invalid parameter
        When I query POST "/applications?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                                                                                                               |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['job', 'validation_type', 'env_specific', 'name', 'build_host', 'deploy_type', 'arch', 'id', 'build_type'].    |
        And there is no application with pkg_name="app4"
        And there is no application with path="myjob"

        Examples:
            | query                         |
            | name=app4&job=myjob&foo=bar   |
            | foo=bar&name=app4&job=myjob   |

    @rest
    Scenario Outline: attempt to violate a unique constraint
        When I query POST "/applications?<query>"
        Then the response code is 409
        And the response contains errors:
            | location  | name      | description                                                                       |
            | query     | <name>    | Unique constraint violated. An application with this <type> already exists.  |

        Examples:
            | query                     | name  | type  |
            | name=app3&job=myjob       | name  | name  |
            | name=app3&id=2&job=myjob  | name  | name  |
            | name=app3&id=2&job=myjob  | id    | ID    |
