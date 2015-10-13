Feature: Update (PUT) package on REST API
    As a developer
    I want to update information for one of my packages
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
    Scenario Outline: update a package for an application that doesn't exist
        Given there is a jenkins job with name="myjob"
        And the job has a build with number="1"
        When I query PUT "/applications/<select>/packages/1/2"
        Then the response code is 404
        And the response contains errors:
            | location  | name          | description                                   |
            | path      | name_or_id    | Application with <descript> does not exist.   |

        Examples:
            | select    | descript      |
            | noexist   | name noexist  |
            | 500       | ID 500        |

    @rest @jenkins_server
    Scenario Outline: update a package that doesn't exist for an application that does
        Given there is a jenkins job with name="myjob"
        And the job has a build with number="1"
        When I query PUT "/applications/<select>/packages/<ver>/<rev>"
        Then the response code is 404
        And the response contains errors:
            | location  | name      | description                                                                           |
            | path      | revision  | Package with version <ver> and revision <rev> does not exist for this application.    |

        Examples:
            | select    | ver   | rev   |
            | app1      | 3     | 500   |
            | 2         | 3     | 500   |
            | app1      | 500   | 1     |
            | 2         | 500   | 1     |

    @rest @jenkins_server
    Scenario Outline: pass an invalid parameter
        Given there is a jenkins job with name="myjob"
        And the job has a build with number="2"
        When I query PUT "/applications/<select>/packages/2/3?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                                                       |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['status', 'builder', 'job', 'version', 'revision'].    |
        And there is a package with version=2,revision=3

        Examples:
            | select    | query                 |
            | app2      | foo=bar               |
            | 3         | foo=bar               |
            | app2      | version=2&foo=bar     |
            | 3         | version=2&foo=bar     |
            | app2      | foo=bar&version=2     |
            | 3         | foo=bar&version=2     |

    @rest @jenkins_server
    Scenario Outline: update a package
        Given there is a jenkins job with name="myjob"
        And the job has a build with number="10"
        When I query PUT "/applications/<select>/packages/2/3?version=10&revision=50"
        Then the response code is 200
        And the response is an object with version="10",revision="50"
        And there is a package with version=10,revision=50

        Examples:
            | select    |
            | app2      |
            | 3         |

    @rest @jenkins_server
    Scenario Outline: attempt to violate a unique constraint
        Given there is a jenkins job with name="myjob"
        And the job has a build with number="2"
        When I query PUT "/applications/<select>/packages/2/3?<query>"
        Then the response code is 409
        And the response contains errors:
            | location  | name      | description                                                                                                       |
            | query     | <name>    | Unique constraint violated. Another package for this application with this version and revision already exists.   |
        And there is a package with version=2,revision=3

        Examples:
            | select    | name      | query                 |
            | app2      | revision  | revision=2            |
            | 3         | revision  | revision=2            |
            | app2      | version   | version=2&revision=2  |
            | 3         | version   | version=2&revision=2  |

    @rest @jenkins_server
    Scenario Outline: attempt to set status to pending from something other than failed
        Given there is a jenkins job with name="myjob"
        And the job has a build with number="3"
        And there are packages:
            | version   | revision  | status    |
            | 3         | 2         | <status>  |
        When I query PUT "/applications/app2/packages/3/2?status=pending"
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
        Given there is a jenkins job with name="myjob"
        And the job has a build with number="3"
        And there are packages:
            | version   | revision  | status    |
            | 3         | 2         | failed    |
        When I query PUT "/applications/app2/packages/3/2?status=pending"
        Then the response code is 200
        And the response is an object with version="3",revision="2",status="pending"
        And there is no package with version=3,revision=2,status="failed"
        And there is a package with version=3,revision=2,status="pending"

    @rest
    Scenario: Jenkins unreachable
        When I query PUT "/applications/app2/packages/3/1?revision=500"
        Then the response code is 500
        And the response contains errors:
            | location  | name          | description                                                                           |
            | path      | name_or_id    | Unable to connect to Jenkins server at https://example.org:8080 to check for package. |
        And there is no package with version="3",revision="500"
        And there is a package with version="3",revision="1"

    @rest @jenkins_server
    Scenario: no matching Jenkins job
        Given there is a jenkins job with name="myjob"
        When I query PUT "/applications/app2/packages/3/1?revision=500&job=somejob"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                           |
            | query     | job   | Jenkins job somejob does not exist.   |
        And there is no package with version="3",revision="500"
        And there is a package with version="3",revision="1"

    @rest @jenkins_server
    Scenario: no matching Jenkins build
        Given there is a jenkins job with name="myjob"
        When I query PUT "/applications/app2/packages/3/1?revision=500"
        Then the response code is 400
        And the response contains errors:
            | location  | name          | description                                                           |
            | path      | name_or_id    | Build with version 3 for job myjob does not exist on Jenkins server.  |
        And there is no package with version=3,revision=500
        And there is a package with version=3,revision=1
