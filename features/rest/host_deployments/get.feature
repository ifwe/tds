Feature: GET host deployment(s) from the REST API
    As a developer
    I want to retrieve host deployments
    So that I can know the current status of the environment

    Background:
        Given I have a cookie with user permissions
        And there is an application with pkg_name="app1"
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | pending   |
        And there is an environment with name="dev"
        And there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |

    @rest
    Scenario: no host deployments
        When I query GET "/host_deployments"
        Then the response code is 200
        And the response is a list of 0 items

    @rest
    Scenario: get host deployment that doesn't exist
        When I query GET "/host_deployments/500"
        Then the response code is 404
        And the response contains errors:
            | location  | name  | description                                   |
            | path      | id    | Host deployment with ID 500 does not exist.   |

    @rest
    Scenario: get all host deployments
        Given there are host deployments:
            | id    | deployment_id | host_id   | status        | user  | package_id    | duration  |
            | 1     | 1             | 1         | pending       | foo   | 1             | 2         |
            | 2     | 1             | 2         | inprogress    | foo   | 1             | 20        |
        When I query GET "/host_deployments"
        Then the response code is 200
        And the response is a list of 2 items
        And the response list contains an object with id=1,deployment_id=1,host_id=1,status="pending",user="foo",package_id=1,duration=2
        And the response list contains an object with id=2,deployment_id=1,host_id=2,status="inprogress",user="foo",package_id=1,duration=20

    @rest
    Scenario: get a specific host deployment
        Given there are host deployments:
            | id    | deployment_id | host_id   | status        | user  | package_id    | duration  |
            | 1     | 1             | 1         | pending       | foo   | 1             | 2         |
            | 2     | 1             | 2         | inprogress    | foo   | 1             | 20        |
        When I query GET "/host_deployments/1"
        Then the response code is 200
        And the response is an object with id=1,deployment_id=1,host_id=1,status="pending",user="foo",package_id=1,duration=2

    @rest
    Scenario Outline: specify limit and/or last queries
        Given there are hosts:
            | name  | env   |
            | host3 | dev   |
            | host4 | dev   |
            | host5 | dev   |
        And there are host deployments:
            | id    | deployment_id | host_id   | status        | user  | package_id    |
            | 1     | 1             | 1         | pending       | foo   | 1             |
            | 2     | 1             | 2         | inprogress    | foo   | 1             |
            | 3     | 1             | 3         | pending       | foo   | 1             |
            | 4     | 1             | 4         | inprogress    | foo   | 1             |
            | 5     | 1             | 5         | pending       | foo   | 1             |
        When I query GET "/host_deployments?limit=<limit>&start=<start>"
        Then the response code is 200
        And the response is a list of <num> items
        And the response list contains id range <min> to <max>

        Examples:
            | limit | start | num   | min   | max   |
            |       |       | 5     | 1     | 5     |
            |       | 1     | 5     | 1     | 5     |
            | 10    |       | 5     | 1     | 5     |
            | 4     | 1     | 4     | 1     | 4     |
            |       |       | 5     | 1     | 5     |
            |       | 2     | 4     | 2     | 5     |
