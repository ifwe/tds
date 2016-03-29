Feature: GET tier deployment(s) from the REST API
    As a developer
    I want to retrieve tier deployments
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
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"

    @rest
    Scenario: no tier deployments
        When I query GET "/tier_deployments"
        Then the response code is 200
        And the response is a list of 0 items

    @rest
    Scenario: get tier deployment that doesn't exist
        When I query GET "/tier_deployments/500"
        Then the response code is 404
        And the response contains errors:
            | location  | name  | description                                   |
            | path      | id    | Tier deployment with ID 500 does not exist.   |

    @rest
    Scenario: get all tier deployments
        Given there are tier deployments:
            | id    | deployment_id | environment_id    | status        | user  | app_id    | package_id    | duration  |
            | 1     | 1             | 1                 | pending       | foo   | 1         | 1             | 2         |
            | 2     | 1             | 1                 | inprogress    | foo   | 2         | 1             | 20        |
        When I query GET "/tier_deployments"
        Then the response code is 200
        And the response is a list of 2 items
        And the response list contains an object with id=1,deployment_id=1,tier_id=1,status="pending",user="foo",environment_id=1,package_id=1,duration=2
        And the response list contains an object with id=2,deployment_id=1,tier_id=2,status="inprogress",user="foo",environment_id=1,package_id=1,duration=20

    @rest
    Scenario: get all tier deployments with select query
        Given there are tier deployments:
            | id    | deployment_id | environment_id    | status        | user  | app_id    | package_id    | duration  |
            | 1     | 1             | 1                 | pending       | foo   | 1         | 1             | 2         |
            | 2     | 1             | 1                 | inprogress    | foo   | 2         | 1             | 20        |
        When I query GET "/tier_deployments?select=id,deployment_id"
        Then the response code is 200
        And the response is a list of 2 items
        And the response list contains an object with id=1,deployment_id=1
        And the response list contains an object with id=2,deployment_id=1
        And the response list objects do not contain attributes tier_id,status,user,environment_id,package_id,duration

    @rest
    Scenario: get a specific tier deployment
        Given there are tier deployments:
            | id    | deployment_id | environment_id    | status        | user  | app_id    | package_id    | duration  |
            | 1     | 1             | 1                 | pending       | foo   | 1         | 1             | 2         |
            | 2     | 1             | 1                 | inprogress    | foo   | 2         | 1             | 20        |
        When I query GET "/tier_deployments/1"
        Then the response code is 200
        And the response is an object with id=1,deployment_id=1,tier_id=1,status="pending",user="foo",environment_id=1,package_id=1,duration=2

    @rest
    Scenario: get a specific tier deployment with select query
        Given there are tier deployments:
            | id    | deployment_id | environment_id    | status        | user  | app_id    | package_id    | duration  |
            | 1     | 1             | 1                 | pending       | foo   | 1         | 1             | 2         |
            | 2     | 1             | 1                 | inprogress    | foo   | 2         | 1             | 20        |
        When I query GET "/tier_deployments/1?select=id,deployment_id"
        Then the response code is 200
        And the response is an object with id=1,deployment_id=1
        And the response object does not contain attributes tier_id,status,user,environment_id,package_id,duration

    @rest
    Scenario Outline: specify limit and/or last queries
        Given there is a deploy target with name="tier3"
        And there is a deploy target with name="tier4"
        And there is a deploy target with name="tier5"
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status        | user  | app_id    | package_id    |
            | 1     | 1             | 1                 | pending       | foo   | 1         | 1             |
            | 2     | 1             | 1                 | inprogress    | foo   | 2         | 1             |
            | 3     | 1             | 1                 | pending       | foo   | 3         | 1             |
            | 4     | 1             | 1                 | inprogress    | foo   | 4         | 1             |
            | 5     | 1             | 1                 | pending       | foo   | 5         | 1             |
        When I query GET "/tier_deployments?limit=<limit>&start=<start>"
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
