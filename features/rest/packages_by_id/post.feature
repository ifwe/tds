Feature: POST package(s) from the REST API by ID
    As a developer
    I want to add a new package
    So that the database has the proper information

    Background:
        Given I have a cookie with user permissions
        And there are applications:
            | name  | path  |
            | app1  | myjob |
            | app2  | myjob |
            | app3  | myjob |
        And there is a package with version=1,revision=1

    @rest @jenkins_server
    Scenario: add a new package
        Given there is a jenkins job with name="myjob"
        And the job has a build with number="2"
        When I query POST "/packages?name=app3&version=2&revision=2"
        Then the response code is 201
        And the response is an object with version="2",revision="2",user="testuser"
        And there is a package with version="2",revision="2",creator="testuser"

    @rest @jenkins_server
    Scenario: omit required field
        Given there is a jenkins job with name="myjob"
        And the job has a build with number="2"
        When I query POST "/packages?version=2&revision=2"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                   |
            | query     |       | name is a required field. |
        And there is no package with version="2",revision="2",creator="testuser"

    @rest @jenkins_server
    Scenario: pass an name for an application that doesn't exist
        Given there is a jenkins job with name="myjob"
        And the job has a build with number="2"
        When I query POST "/packages?name=noexist&version=2&revision=2"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                                   |
            | query     | name  | Application with name noexist does not exist. |
        And there is no package with version="2",revision="2",creator="testuser"

    @rest @jenkins_server
    Scenario: pass an invalid parameter
        Given there is a jenkins job with name="myjob"
        And the job has a build with number="2"
        When I query POST "/packages?name=app3&version=2&revision=2&foo=bar"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                                                                   |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['builder', 'id', 'job', 'name', 'revision', 'status', 'version'].  |
        And there is no package with version="2",revision="2",creator="testuser"

    @rest @jenkins_server
    Scenario: attempt to violate a unique constraint
        Given there is a jenkins job with name="myjob"
        And the job has a build with number="1"
        When I query POST "/packages?name=app3&version=1&revision=1"
        Then the response code is 409
        And the response contains errors:
            | location  | name      | description                                                                                               |
            | query     | version   | Unique constraint violated. A package for this application with this version and revision already exists. |

    @rest @jenkins_server
    Scenario Outline: attempt to set status to something other than pending
        Given there is a jenkins job with name="myjob"
        And the job has a build with number="2"
        When I query POST "/packages?name=app3&version=2&revision=2&status=<status>"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                               |
            | query     | status    | Status must be pending for new packages.  |
        And there is no package with version="2",revision="2",creator="testuser"

        Examples:
            | status        |
            | processing    |
            | failed        |
            | completed     |
            | removed       |

    @rest
    Scenario: Jenkins unreachable
        When I query POST "/packages?name=app3&version=2&revision=2"
        Then the response code is 500
        And the response contains errors:
            | location  | name      | description                                                                           |
            | query     | version   | Unable to connect to Jenkins server at https://example.org:8080 to check for package. |
        And there is no package with version="2",revision="2",creator="testuser"

    @rest @jenkins_server
    Scenario Outline: no matching Jenkins job
        When I query POST "/packages?name=app3&version=2&revision=2&<query>"
        Then the response code is 400
        And the response contains errors:
            | location  | name      | description                       |
            | <loc>     | <name>    | Jenkins job <job> does not exist. |
        And there is no package with version="2",revision="2",creator="testuser"

        Examples:
            | query         | loc   | name      | job       |
            |               | query | version   | myjob     |
            | job=somejob   | query | job       | somejob   |

    @rest @jenkins_server
    Scenario: no matching Jenkins build
        Given there is a jenkins job with name="myjob"
        When I query POST "/packages?name=app3&version=2&revision=2"
        Then the response code is 400
        And the response contains errors:
            | location  | name      | description                                                           |
            | query     | version   | Build with version 2 for job myjob does not exist on Jenkins server.  |
        And there is no package with version="2",revision="2",creator="testuser"
