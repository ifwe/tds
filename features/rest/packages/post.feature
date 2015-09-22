Feature: Add (POST) package on REST API
    As a developer
    I want to add a new package
    So that the database has the proper information

    Background:
        Given there are applications:
            | name  | path  |
            | app1  | myjob |
            | app2  | myjob |
            | app3  | myjob |
        And there is a package with version=1,revision=1
        And I have a cookie with user permissions

    @rest @jenkins_server
    Scenario Outline: add a new package
        Given there is a jenkins job with name="myjob"
        And the job has a build with number="2"
        When I query POST "/applications/<select>/packages?version=<ver>&revision=<rev>"
        Then the response code is 201
        And the response is an object with version="<ver>",revision="<rev>",creator="testuser",job="myjob"
        And there is a package with version="<ver>",revision="<rev>",creator="testuser",job="myjob"

        Examples:
            | select    | ver   | rev   |
            | app3      | 2     | 2     |
            | 4         | 2     | 2     |

    @rest @jenkins_server
    Scenario: specify job
        Given there is a jenkins job with name="somejob"
        And the job has a build with number="2"
        When I query POST "/applications/4/packages?version=2&revision=2&job=somejob"
        Then the response code is 201
        And the response is an object with version="2",revision="2",creator="testuser",job="somejob"
        And there is a package with version="2",revision="2",creator="testuser",job="somejob"

    @rest @jenkins_server
    Scenario: specify id
        Given there is a jenkins job with name="myjob"
        And the job has a build with number="2"
        When I query POST "/applications/app3/packages?version=2&revision=2&id=10"
        Then the response code is 201
        And the response is an object with version="2",revision="2",id=10,creator="testuser"
        And there is a package with version="2",revision="2",id=10,creator="testuser"

    @rest @jenkins_server
    Scenario: omit required field
        Given there is a jenkins job with name="myjob"
        And the job has a build with number="2"
        When I query POST "/applications/app3/packages?revision=2"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                   |
            | query     |       | version is a required field.  |
        And there is no package with version="2",revision="2",creator="testuser"

    @rest @jenkins_server
    Scenario Outline: pass an invalid parameter
        Given there is a jenkins job with name="myjob"
        And the job has a build with number="2"
        When I query POST "/applications/app3/packages?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                                                           |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['status', 'builder', 'job', 'version', 'id', 'revision'].  |
        And there is no package with version="2",revision="2",creator="testuser"

        Examples:
            | query                         |
            | version=2&revision=2&foo=bar  |
            | foo=bar&version=2&revision=2  |

    @rest @jenkins_server
    Scenario Outline: attempt to violate a unique constraint
        Given there is a jenkins job with name="myjob"
        And the job has a build with number="<num>"
        When I query POST "/applications/app3/packages?<query>"
        Then the response code is 409
        And the response contains errors:
            | location  | name      | description                                                   |
            | query     | <name>    | Unique constraint violated. A package <type> already exists.  |

        Examples:
            | num   | query                     | name      | type                                                  |
            | 1     | version=1&revision=1      | version   | for this application with this version and revision   |
            | 1     | version=1&revision=1&id=3 | version   | for this application with this version and revision   |
            | 2     | version=2&revision=2&id=1 | id        | with this ID                                          |

    @rest @jenkins_server
    Scenario Outline: attempt to set status to something other than pending
        Given there is a jenkins job with name="myjob"
        And the job has a build with number="2"
        When I query POST "/applications/app3/packages?version=2&revision=2&status=<status>"
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
        When I query POST "/applications/4/packages?version=2&revision=2"
        Then the response code is 500
        And the response contains errors:
            | location  | name          | description                                                                           |
            | path      | name_or_id    | Unable to connect to Jenkins server at https://example.org:8080 to check for package. |
        And there is no package with version="2",revision="2",creator="testuser"

    @rest @jenkins_server
    Scenario: no matching Jenkins job
        When I query POST "/applications/4/packages?version=2&revision=2"
        Then the response code is 400
        And the response contains errors:
            | location  | name          | description                       |
            | path      | name_or_id    | Jenkins job myjob does not exist. |
        And there is no package with version="2",revision="2",creator="testuser"

    @rest @jenkins_server
    Scenario: no matching Jenkins build
        Given there is a jenkins job with name="myjob"
        When I query POST "/applications/4/packages?version=2&revision=2"
        Then the response code is 400
        And the response contains errors:
            | location  | name          | description                                                           |
            | path      | name_or_id    | Build with version 2 for job myjob does not exist on Jenkins server.  |
        And there is no package with version="2",revision="2",creator="testuser"
