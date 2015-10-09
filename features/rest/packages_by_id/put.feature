Feature: Update (PUT) package on REST API by ID
    As a developer
    I want to update information for a package
    So that the database has the proper information

    Background:
        Given there are applications:
            | name  | path  |
            | app1  | myjob |
            | app2  | myjob |
        And there are packages:
            | version   | revision  | job   |
            | 1         | 2         | myjob |
            | 2         | 1         | myjob |
            | 2         | 2         | myjob |
            | 2         | 3         | myjob |
            | 3         | 1         | myjob |
        And I have a cookie with user permissions

    @rest @jenkins_server
    Scenario: update a package that doesn't exist
        Given there is a jenkins job with name="myjob"
        And the job has a build with number="500"
        When I query PUT "/packages/500?version=500"
        Then the response code is 404
        And the response contains errors:
            | location  | name  | description                           |
            | path      | id    | Package with ID 500 does not exist.   |
        And there is no package with version="500"

    @rest @jenkins_server
    Scenario: pass an invalid parameter
        Given there is a jenkins job with name="myjob"
        And the job has a build with number="500"
        When I query PUT "/packages/1?foo=bar&version=500"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                                                                       |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['status', 'name', 'builder', 'job', 'version', 'id', 'revision'].  |
        And there is no package with version="500"

    @rest @jenkins_server
    Scenario: update a package
        Given there is a jenkins job with name="myjob"
        And the job has a build with number="1"
        When I query PUT "/packages/1?name=app1"
        Then the response code is 200
        And the response is an object with name="app1"
        And there is a package with pkg_name="app1"

    @rest @jenkins_server
    Scenario Outline: attempt to violate a unique constraint
        Given there is an application with name="app3",path="myjob"
        And there is a jenkins job with name="myjob"
        And the job has a build with number="2"
        And there are packages:
            | version   | revision  | job   |
            | 2         | 2         | myjob |
            | 2         | 3         | myjob |
        When I query PUT "/packages/4?revision=2&<query>"
        Then the response code is 409
        And the response contains errors:
            | location  | name      | description                                                                                                       |
            | query     | <name>    | Unique constraint violated. Another package for this application with this version and revision already exists.   |
        And there is a package with version=2,revision=3,pkg_name="app2"

        Examples:
            | query                 | name          |
            |                       | revision      |
            | version=2             | version       |
            | name=app3&version=2   | name          |

    @rest @jenkins_server
    Scenario Outline: attempt to set status to pending from something other than failed
        Given there are packages:
            | version   | revision  | status    | job   |
            | 3         | 2         | <status>  | myjob |
        And there is a jenkins job with name="myjob"
        And the job has a build with number="3"
        When I query PUT "/packages/6?status=pending"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                       |
            | query     | status    | Cannot change status to pending from <status>.    |
        And there is no package with version=3,revision=2,status="pending"
        And there is a package with version=3,revision=2,status="<status>"

        Examples:
            | status        |
            | processing    |
            | completed     |
            | removed       |

    @rest @jenkins_server
    Scenario: change status back to pending from failed
        Given there are packages:
            | version   | revision  | status    | job   |
            | 3         | 2         | failed    | myjob |
        And there is a jenkins job with name="myjob"
        And the job has a build with number="3"
        When I query PUT "/packages/6?status=pending"
        Then the response code is 200
        And the response is an object with version="3",revision="2",status="pending"
        And there is no package with version=3,revision=2,status="failed"
        And there is a package with version=3,revision=2,status="pending"

    @rest
    Scenario: Jenkins unreachable
        When I query PUT "/packages/1?version=500"
        Then the response code is 500
        And the response contains errors:
            | location  | name      | description                                                                           |
            | query     | version   | Unable to connect to Jenkins server at https://example.org:8080 to check for package. |
        And there is no package with version=500
        And there is a package with version=1

    @rest @jenkins_server
    Scenario: no matching Jenkins job
        Given there is a jenkins job with name="myjob"
        When I query PUT "/packages/2?job=somejob"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                           |
            | query     | job   | Jenkins job somejob does not exist.   |
        And there is no package with id=2,job="somejob"
        And there is a package with id=2,job="myjob"

    @rest @jenkins_server
    Scenario: no matching Jenkins build
        Given there is a jenkins job with name="myjob"
        When I query PUT "/packages/2?revision=500"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                                                           |
            | path      | id    | Build with version 2 for job myjob does not exist on Jenkins server.  |
        And there is no package with revision=200
        And there is a package with revision=1
