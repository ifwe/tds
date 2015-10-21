Feature: GET application(s) from the REST API
    As a developer
    I want information on applications
    So that I can be informed of the current state of the database

    Background:
        Given I have a cookie with user permissions

    @rest
    Scenario: no applications
        When I query GET "/applications"
        Then the response code is 200
        And the response is a list of 0 items

    @rest
    Scenario Outline: get an application that doesn't exist
        When I query GET "/applications/<select>"
        Then the response code is 404
        And the response contains errors:
            | location  | name          | description                                   |
            | path      | name_or_id    | Application with <descript> does not exist.   |

        Examples:
            | select    | descript      |
            | noexist   | name noexist  |
            | 500       | ID 500        |

    @rest
    Scenario: get all applications
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
            | app3  |
        When I query GET "/applications"
        Then the response code is 200
        And the response is a list of 3 items
        And the response list contains objects:
            | name  |
            | app1  |
            | app2  |
            | app3  |

    @rest
    Scenario Outline: get a single application by name
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
            | app3  |
        When I query GET "/applications/<app>"
        Then the response code is 200
        And the response is an object with name="<app>"

        Examples:
            | app   |
            | app1  |
            | app2  |
            | app3  |

    @rest
    Scenario Outline: get a single application by ID
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
            | app3  |
        When I query GET "/applications/<id>"
        Then the response code is 200
        And the response is an object with id=<id>

        Examples:
            | id    |
            | 1     |
            | 2     |
            | 3     |

    @rest
    Scenario Outline: pass select query for individual application
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
            | app3  |
        When I query GET "/applications/app1?select=<select>"
        Then the response code is 200
        And the response is an object with <params>
        And the response object does not contain attributes <attrs>

        Examples:
            | select    | params                | attrs                                                                 |
            | name      | name="app1"           | job,arch,build_type,build_host,validation_type,env_specific,created   |
            | name,job  | name="app1",job="job" | arch,build_type,build_host,validation_type,env_specific,created       |

    @rest
    Scenario Outline: pass select query for collection of applications
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
            | app3  |
        When I query GET "/applications?select=<select>"
        Then the response code is 200
        And the response is a list of 3 items
        And the response list contains objects:
            | name  |
            | app1  |
            | app2  |
            | app3  |
        And the response list objects do not contain attributes <attrs>

        Examples:
            | select    | attrs                                                                 |
            | name      | job,arch,build_type,build_host,validation_type,env_specific,created   |
            | name,job  | arch,build_type,build_host,validation_type,env_specific,created       |

    @rest
    Scenario: pass invalid attr to select
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
            | app3  |
        When I query GET "/applications?select=foo"
        Then the response code is 400
        And the response contains errors:
            | location  | name      | description                                                                                                                                                   |
            | query     | select    | foo is not a valid attribute. Valid attributes: ['arch', 'build_host', 'build_type', 'deploy_type', 'env_specific', 'id', 'job', 'name', 'validation_type'].  |

    @rest
    Scenario Outline: specify limit and/or last queries
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
            | app3  |
            | app4  |
            | app5  |
        When I query GET "/applications?limit=<limit>&start=<start>"
        Then the response code is 200
        And the response is a list of <num> items
        And the response list contains id range <min> to <max>

        Examples:
            | limit | start | num   | min   | max   |
            |       |       | 5     | 2     | 6     |
            |       | 2     | 5     | 2     | 6     |
            | 10    |       | 5     | 2     | 6     |
            | 4     | 1     | 4     | 2     | 5     |

    @rest
    Scenario Outline: specify unknown query
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
        When I query GET "/applications?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                               |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['limit', 'select', 'start'].   |

        Examples:
            | query             |
            | foo=bar           |
            | limit=10&foo=bar  |
            | foo=bar&start=2   |
