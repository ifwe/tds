Feature: deploy daemon
    As a deploy daemon
    I want to deploy queued deployments
    So that software can be deployed where needed

    Background:
        Given there are environments
            | name  |
            | dev   |
            | stage |
        And there is a project with name="proj"
        And there is an application with name="myapp"
        And there is a deploy target with name="tier1"
        And I am in the "dev" environment
        And there are hosts:
            | name  | env   | app_id    |
            | host1 | dev   | 2         |
        And there are packages:
            | version   | revision  |
            | 121       | 1         |
        And there are deployments:
            | id    | user  | status        |
            | 1     | foo   | complete      |
            | 2     | foo   | failed        |
            | 3     | foo   | inprogress    |
            | 4     | foo   | pending       |
            | 5     | foo   | canceled      |
        And there are tier deployments:
            | id    | deployment_id | status        | user  | app_id    | package_id    | environment_id    |
            | 1     | 1             | validated     | foo   | 2         | 1             | 1                 |
            | 2     | 2             | incomplete    | foo   | 2         | 1             | 1                 |
            | 3     | 3             | inprogress    | foo   | 2         | 1             | 1                 |
            | 4     | 4             | pending       | foo   | 2         | 1             | 1                 |
            | 5     | 5             | pending       | foo   | 2         | 1             | 1                 |
        And there are host deployments:
            | id    | deployment_id | status        | user  | host_id   | package_id    |
            | 1     | 1             | ok            | foo   | 1         | 1             |
            | 2     | 2             | failed        | foo   | 1         | 1             |
            | 3     | 3             | inprogress    | foo   | 1         | 1             |
            | 4     | 4             | pending       | foo   | 1         | 1             |
            | 5     | 5             | pending       | foo   | 1         | 1             |

    Scenario Outline: run deamon with no queued deployments
        Given the deploy strategy is "<strategy>"
        When I run "deploy_daemon"
        Then there were no deployments run

        Examples:
            | strategy  |
            | salt      |
            | mco       |

    Scenario Outline: run deamon with a tier deployment with no hosts
        Given there is a deploy target with name="tier2"
        And there are deployments:
            | id    | user  | status    |
            | 6     | foo   | queued    |
        And there are tier deployments:
            | id    | deployment_id | status    | user  | app_id    | package_id    | environment_id    |
            | 6     | 6             | <tier_st> | foo   | 3         | 1             | 1                 |
        And the deploy strategy is "<strategy>"
        When I run "deploy_daemon"
        Then there is a deployment with id=6,status="complete"
        And there is a tier deployment with id=6,deployment_id=6,status="complete"

        Examples:
            | strategy  | tier_st       |
            | salt      | pending       |
            | salt      | incomplete    |
            | mco       | pending       |
            | mco       | incomplete    |

    Scenario Outline: run deamon with a tier deployment with hosts
        Given there are deployments:
            | id    | user  | status    |
            | 6     | foo   | queued    |
        And there are tier deployments:
            | id    | deployment_id | status    | user  | app_id    | package_id    | environment_id    |
            | 6     | 6             | <tier_st> | foo   | 2         | 1             | 1                 |
        And there are host deployments:
            | id    | deployment_id | status    | user  | host_id   | package_id    |
            | 6     | 6             | <host_st> | foo   | 1         | 1             |
        And the deploy strategy is "<strategy>"
        When I run "deploy_daemon"
        Then there is a deployment with id=6,status="complete"
        And there is a tier deployment with id=6,deployment_id=6,status="complete"
        And there is a host deployment with id=6,deployment_id=6,status="ok"
        And package "myapp" version "121" was deployed to the deploy target with name="tier1"

        Examples:
            | strategy  | tier_st       | host_st   |
            | salt      | pending       | pending   |
            | salt      | incomplete    | failed    |
            | salt      | incomplete    | pending   |
            | mco       | pending       | pending   |
            | mco       | incomplete    | failed    |
            | mco       | incomplete    | pending   |

    Scenario Outline: run deamon with multiple tier & host deployments
        Given there is a deploy target with name="tier2"
        And there are hosts:
            | name  | env   | app_id    |
            | host2 | dev   | 3         |
            | host3 | dev   | 3         |
        And there are deployments:
            | id    | user  | status    |
            | 6     | foo   | queued    |
        And there are tier deployments:
            | id    | deployment_id | status    | user  | app_id    | package_id    | environment_id    |
            | 6     | 6             | pending   | foo   | 2         | 1             | 1                 |
            | 7     | 6             | <tier_st> | foo   | 3         | 1             | 1                 |
        And there are host deployments:
            | id    | deployment_id | status    | user  | host_id   | package_id    |
            | 6     | 6             | pending   | foo   | 1         | 1             |
            | 7     | 6             | <host_st> | foo   | 2         | 1             |
            | 8     | 6             | ok        | foo   | 3         | 1             |
        And the deploy strategy is "<strategy>"
        When I run "deploy_daemon"
        Then there is a deployment with id=6,status="complete"
        And there is a tier deployment with id=6,deployment_id=6,status="complete"
        And there is a tier deployment with id=7,deployment_id=6,status="complete"
        And there is a host deployment with id=6,deployment_id=6,status="ok"
        And there is a host deployment with id=7,deployment_id=6,status="ok"
        And there is a host deployment with id=8,deployment_id=6,status="ok"
        And package "myapp" version "121" was deployed to the deploy target with name="tier1"
        And package "myapp" version "121" was deployed to host "host2"

        Examples:
            | strategy  | tier_st       | host_st   |
            | salt      | pending       | pending   |
            | salt      | incomplete    | failed    |
            | salt      | incomplete    | pending   |
            | mco       | pending       | pending   |
            | mco       | incomplete    | failed    |
            | mco       | incomplete    | pending   |