Feature: deploy fix application [--delay] [--hosts|--apptypes|--all-apptypes]
    As a developer
    I want to fix failed deployments to targets
    So I can complete a given deployment fully

    Background:
        Given I have "stage" permissions
        And there are environments
            | name   |
            | dev    |
            | stage  |
        And I am in the "stage" environment
        And there is a project with name="proj"
        And there is an application with name="myapp"
        And there is a deploy target with name="the-apptype"
        And the tier "the-apptype" is associated with the application "myapp" for the project "proj"
        And there are hosts:
            | name          | env     | app_id  |
            | dprojhost01   | dev     | 2       |
            | dprojhost02   | dev     | 2       |
            | sprojhost01   | stage   | 2       |
            | sprojhost02   | stage   | 2       |

        And there are packages:
            | version   | revision  |
            | 122       | 1         |
            | 123       | 1         |
        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | complete  |
            | 2     | foo   | complete  |
            | 3     | foo   | failed    |
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status    | user  | app_id    | package_id    |
            | 1     | 1             | 2                 | validated | foo   | 2         | 1             |
        And I wait 1 seconds
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status    | user  | app_id    | package_id    |
            | 2     | 2             | 1                 | validated | foo   | 2         | 2             |
        And I wait 1 seconds
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status        | user  | app_id    | package_id    |
            | 3     | 3             | 2                 | incomplete    | foo   | 2         | 2             |
        And there are host deployments:
            | id    | deployment_id | status    | user  | host_id   | package_id    |
            | 1     | 3             | failed    | foo   | 4         | 2             |
            | 2     | 3             | ok        | foo   | 3         | 2             |

    Scenario: fix application that doesn't exist
        When I run "deploy fix badapp"
        Then the output has "Application does not exist: badapp"

    Scenario: fix to host that doesn't exist
        When I run "deploy fix myapp --hosts badhost01"
        Then the output has "Host does not exist: badhost01"

    Scenario: fix to apptype that doesn't exist
        When I run "deploy fix myapp --apptype bad-apptype"
        Then the output has "Valid apptypes for application "myapp" are: ['the-apptype']"

    Scenario: fix to hosts
        When I run "deploy fix myapp --hosts sprojhost02"
        Then the output has "Deployment now being run, press Ctrl-C at any time to cancel..."
        And there is a deployment with id=4,status="queued",delay=0
        And there is no tier deployment with deployment_id=4
        And there is a host deployment with status="pending",deployment_id=4,host_id=4,package_id=2

    Scenario: fix to apptype
        When I run "deploy fix myapp --apptype the-apptype"
        Then the output has "Deployment now being run, press Ctrl-C at any time to cancel..."
        And there is a deployment with id=4,status="queued",delay=0
        And there is a tier deployment with deployment_id=4,app_id=2,status="pending",package_id=2,environment_id=2
        And there is no host deployment with deployment_id=4,host_id=3
        And there is a host deployment with status="pending",deployment_id=4,host_id=4,package_id=2

    Scenario: fix to all apptypes
        Given there is a deploy target with name="another-apptype"
        And there are hosts:
            | name          | env   | app_id    |
            | anotherhost01 | stage | 3         |
        And the tier "another-apptype" is associated with the application "myapp" for the project "proj"
        And there are deployments:
            | id    | user  | status    |
            | 4     | foo   | failed    |
        And I wait 1 seconds
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status        | user  | app_id    | package_id    |
            | 4     | 4             | 2                 | incomplete    | foo   | 3         | 2             |
        And there are host deployments:
            | id    | deployment_id | status    | user  | host_id   | package_id    |
            | 3     | 4             | failed    | foo   | 5         | 2             |
        When I run "deploy fix myapp --all-apptypes"
        Then the output has "Deployment now being run, press Ctrl-C at any time to cancel..."
        And there is a deployment with id=5,status="queued",delay=0
        And there is no tier deployment with deployment_id=5,environment_id=1
        And there is no tier deployment with deployment_id=5,app_id=2,environment_id=1
        And there is no host deployment with deployment_id=5,host_id=1
        And there is no host deployment with deployment_id=5,host_id=2
        And there is no host deployment with deployment_id=5,host_id=3
        And there is a tier deployment with deployment_id=5,app_id=2,status="pending",package_id=2,environment_id=2
        And there is a tier deployment with deployment_id=5,app_id=3,status="pending",package_id=2,environment_id=2
        And there is a host deployment with deployment_id=5,host_id=4,package_id=2,status="pending"
        And there is a host deployment with deployment_id=5,host_id=5,package_id=2,status="pending"

    #TODO: Figure out what to do with these tests
    # Scenario: fix to host with a failure
    #     Given the host "sprojhost02" will fail to deploy
    #     When I run "deploy fix myapp --hosts sprojhost02"
    #     Then the output has "Some hosts had failures"
    #     And the output has "Hostname: sprojhost02"
    #
    # Scenario: fix to apptype with a failure
    #     Given the host "sprojhost02" will fail to deploy
    #     When I run "deploy fix myapp --apptype the-apptype"
    #     Then the output has "Some hosts had failures"
    #     And the output has "Hostname: sprojhost02"
    #
    # Scenario: fix to all apptypes with a failure
    #     Given the host "sprojhost02" will fail to deploy
    #     When I run "deploy fix myapp --all-apptypes"
    #     Then the output has "Some hosts had failures"
    #     And the output has "Hostname: sprojhost02"

    Scenario: fix with delay option
        When I run "deploy fix myapp --delay 10"
        Then the output has "Deployment now being run, press Ctrl-C at any time to cancel..."
        And there is a deployment with id=4,status="queued",delay=10
        And there is a tier deployment with deployment_id=4,status="pending",app_id=2,package_id=2,environment_id=2
        And there is a host deployment with deployment_id=4,status="pending",host_id=4,package_id=2

    Scenario: TDS-51
        Given I am in the "dev" environment
        And there is a package with version="124"
        And there are deployments:
            | id    | user  | status    |
            | 4     | foo   | failed    |
        And I wait 1 seconds
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status        | user  | app_id    | package_id    |
            | 4     | 4             | 1                 | incomplete    | foo   | 2         | 3             |
        And there are host deployments:
            | id    | deployment_id | status    | user  | host_id   | package_id    |
            | 3     | 4             | failed    | foo   | 1         | 3             |
            | 4     | 4             | ok        | foo   | 2         | 3             |
        When I run "deploy fix myapp --apptypes the-apptype"
        Then the output has "Deployment now being run, press Ctrl-C at any time to cancel..."
        And there is a deployment with id=5,status="queued",delay=0
        And there is a tier deployment with deployment_id=5,status="pending",app_id=2,package_id=3,environment_id=1
        And there is no tier deployment with deployment_id=5,environment_id=2
        And there is a host deployment with deployment_id=5,status="pending",host_id=1,package_id=3
        And there is no host deployment with deployment_id=5,host_id=2
        And there is no host deployment with deployment_id=5,host_id=3
        And there is no host deployment with deployment_id=5,host_id=4
