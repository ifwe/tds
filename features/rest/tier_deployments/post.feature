Feature: POST tier deployment(s) from the REST API
    As a developer
    I want to add tier deployments
    So that I can put my software on tiers

    Background:
        Given I have a cookie with user permissions
        And there is an application with pkg_name="app1"
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
            | 1         | 2         |
        And there are deployments:
            | id    | user  | package_id    | status    |
            | 1     | foo   | 1             | pending   |
        And there is an environment with name="dev"
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"

    @rest
    Scenario: post a tier deployment
        When I query POST "/tier_deployments?deployment_id=1&tier_id=1&environment_id=1"
        Then the response code is 201
        And the response is an object with deployment_id=1,tier_id=1,id=1,user="testuser",environment_id=1
        And there is a tier deployment with deployment_id=1,app_id=1,id=1,user="testuser",environment_id=1

    @rest
    Scenario: omit required field
        When I query POST "/tier_deployments?deployment_id=1"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                           |
            | query     |       | tier_id is a required field.          |
            | query     |       | environment_id is a required field.   |
        And there is no tier deployment with deployment_id=1,id=1

    @rest
    Scenario Outline: attempt to set the status to not pending
        When I query POST "/tier_deployments?deployment_id=1&tier_id=1&environment_id=1&status=<status>"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                       |
            | query     | status    | Status must be pending for new tier deployments.  |
        And there is no tier deployment with deployment_id=1,app_id=1,status="<status>",environment_id=1

        Examples:
            | status        |
            | inprogress    |
            | failed        |
            | ok            |

    @rest
    Scenario: attempt to violate a unique constraint
        Given there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    |
            | 1     | 1             | 1         | pending   | foo   | 1                 |
        When I query POST "/tier_deployments?id=1&deployment_id=1&tier_id=1&environment_id=1"
        Then the response code is 409
        And the response contains errors:
            | location  | name  | description                                                                   |
            | query     | id    | Unique constraint violated. A tier deployment with this ID already exists.    |

    @rest
    Scenario: pass a tier_id for a tier that doesn't exist
        When I query POST "/tier_deployments?deployment_id=1&tier_id=500&environment_id=1"
        Then the response code is 400
        And the response contains errors:
            | location  | name      | description                   |
            | query     | tier_id   | No tier with ID 500 exists.   |
        And there is no tier deployment with deployment_id=1,app_id=500,environment_id=1

    @rest
    Scenario: pass an environment_id for an environment that doesn't exist
        When I query POST "/tier_deployments?deployment_id=1&tier_id=1&environment_id=500"
        Then the response code is 400
        And the response contains errors:
            | location  | name              | description                           |
            | query     | environment_id    | No environment with ID 500 exists.    |
        And there is no tier deployment with deployment_id=1,app_id=1,environment_id=500

    @rest
    Scenario: attempt to violate (deployment_id, tier_id) unique together constraint
        Given there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    |
            | 1     | 1             | 1         | pending   | foo   | 1                 |
        When I query POST "/tier_deployments?deployment_id=1&tier_id=1&environment_id=1"
        Then the response code is 409
        And the response contains errors:
            | location  | name      | description                                                                                               |
            | query     | tier_id   | ('deployment_id', 'tier_id') are unique together. A tier deployment with these attributes already exists. |
        And there is no tier deployment with id=2

    @rest
    Scenario: attempt to add a tier deployment such that its environment conflicts with that of the deployment
        Given there is an environment with name="staging"
        And there are hosts:
            | name  | env       |
            | host1 | staging   |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  |
            | 1     | 1             | 1         | pending   | foo   |
        And there is a deploy target with name="tier1"
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    |
            | 1     | 1             | 1         | pending   | foo   | 2                 |
        When I query POST "/tier_deployments?deployment_id=1&tier_id=2&environment_id=1"
        Then the response code is 409
        And the response contains errors:
            | location  | name              | description                                                                                                                                                   |
            | query     | environment_id    | Cannot deploy to different environments with same deployment. There is a host deployment associated with this deployment with ID 1 and environment staging.   |
            | query     | environment_id    | Cannot deploy to different environments with same deployment. There is a tier deployment associated with this deployment with ID 1 and environment staging.   |
        And there is no tier deployment with deployment_id=1,app_id=2,environment_id=1
