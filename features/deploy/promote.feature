Feature: deploy promote application version [-f|--force] [--delay] [--hosts|--apptypes|--all-apptypes] [--detach] (-f/--force only for deploy promote)
    As a developer
    I want to deploy applications to targets
    So that I can update services easily

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
        And there are packages:
            | version   | revision  |
            | 121       | 1         |
            | 122       | 1         |
            | 123       | 1         |
        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | complete  |
            | 2     | foo   | complete  |
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status    | user  | app_id    | package_id    |
            | 1     | 1             | 1                 | validated | foo   | 2         | 1             |
        And I wait 1 seconds
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status    | user  | app_id    | package_id    |
            | 2     | 2             | 2                 | validated | foo   | 2         | 2             |
        And I wait 1 seconds
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status    | user  | app_id    | package_id    |
            | 3     | 1             | 1                 | validated | foo   | 2         | 3             |
        And there are hosts:
            | name          | env   | app_id    |
            | dprojhost01   | dev   | 2         |
            | dprojhost02   | dev   | 2         |
            | sprojhost01   | stage | 2         |
            | sprojhost02   | stage | 2         |
        And the tier "the-apptype" is associated with the application "myapp" for the project "proj"

    Scenario: promote application that doesn't exist
        When I run "deploy promote badapp 456 --detach"
        Then the output is "Application does not exist: badapp"

    Scenario: promote version that doesn't exist
        When I run "deploy promote myapp 456 --detach"
        Then the output is "Package does not exist: myapp@456"

    Scenario: promote version to host that doesn't exist
        When I run "deploy promote myapp 123 --hosts badhost01 --detach"
        Then the output has "Host does not exist: badhost01"

    Scenario: promote version to apptype that doesn't exist
        When I run "deploy promote myapp 123 --apptype bad-apptype --detach"
        Then the output has "Valid apptypes for application "myapp" are: ['the-apptype']"

    Scenario: promote version to apptype that's not a part of the project
        Given there is a deploy target with name="other-apptype"
        When I run "deploy promote myapp 123 --apptype other-apptype --detach"
        Then the output has "Valid apptypes for application "myapp" are: ['the-apptype']"

    Scenario: promote version that isn't validated in previous env (only for deploy)
        Given there is a package with version="124"
        When I run "deploy promote myapp 124 --detach"
        Then the output has "Application "myapp", version "124" is not validated in the previous environment for tier "the-apptype", skipping..."

    Scenario: promote version to hosts
        When I run "deploy promote myapp 123 --hosts sprojhost01 sprojhost02 --detach"
        Then the output has "Deployment ready for installer daemon, disconnecting now."
        And there is a deployment with status="queued",delay=0
        And there is a host deployment with status="pending",deployment_id=3,host_id=3,package_id=3
        And there is a host deployment with status="pending",deployment_id=3,host_id=4,package_id=3

    Scenario: promote version to hosts
        When I run "deploy promote myapp 123 --hosts sprojhost01 sprojhost02 --detach"
        Then the output has "Deployment ready for installer daemon, disconnecting now."
        And there is a host deployment with status="pending",deployment_id=3,host_id=3,package_id=3
        And there is a host deployment with status="pending",deployment_id=3,host_id=4,package_id=3

    Scenario: promote older version to hosts
        When I run "deploy promote myapp 121 --hosts sprojhost01 sprojhost02 --detach"
        Then the output has "Deployment ready for installer daemon, disconnecting now."
        And there is a deployment with status="queued",delay=0
        And there is a host deployment with status="pending",deployment_id=3,host_id=3,package_id=1
        And there is a host deployment with status="pending",deployment_id=3,host_id=4,package_id=1

    Scenario: promote version to apptype
        When I run "deploy promote myapp 123 --apptype the-apptype --detach"
        Then the output has "Deployment ready for installer daemon, disconnecting now."
        And there is a deployment with status="queued",delay=0
        And there is a tier deployment with status="pending",deployment_id=3,app_id=2,package_id=3,environment_id=2
        And there is a host deployment with status="pending",deployment_id=3,host_id=3,package_id=3
        And there is a host deployment with status="pending",deployment_id=3,host_id=4,package_id=3
        And there is no tier deployment with deployment_id=3,environment_id=1
        And there is no host deployment with deployment_id=3,host_id=1
        And there is no host deployment with deployment_id=3,host_id=2

    Scenario: promote version to apptype
        When I run "deploy promote myapp 123 --apptype the-apptype --detach"
        Then the output has "Deployment ready for installer daemon, disconnecting now."
        And there is a deployment with status="queued",delay=0
        And there is a tier deployment with status="pending",deployment_id=3,app_id=2,package_id=3,environment_id=2

    Scenario: promote olders version to apptype
        When I run "deploy promote myapp 121 --apptype the-apptype --detach"
        Then the output has "Deployment ready for installer daemon, disconnecting now."
        And there is a deployment with status="queued",delay=0
        And there is a tier deployment with status="pending",deployment_id=3,app_id=2,package_id=1,environment_id=2

    Scenario: promote version to all apptypes
        Given there is a deploy target with name="another-apptype"
        And there is a host with name="anotherhost01"
        And the host is associated with the deploy target
        And the tier "another-apptype" is associated with the application "myapp" for the project "proj"
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status    | user  | app_id    | package_id    |
            | 4     | 2             | 1                 | validated | foo   | 3         | 3             |
        When I run "deploy promote myapp 123 --all-apptypes --detach"
        Then the output has "Deployment ready for installer daemon, disconnecting now."
        And there is a deployment with status="queued",delay=0
        And there is a tier deployment with status="pending",deployment_id=3,app_id=2,package_id=3,environment_id=2
        And there is a tier deployment with status="pending",deployment_id=3,app_id=3,package_id=3,environment_id=2
        And there is a host deployment with status="pending",deployment_id=3,host_id=3,package_id=3
        And there is a host deployment with status="pending",deployment_id=3,host_id=4,package_id=3
        And there is a host deployment with status="pending",deployment_id=3,host_id=5,package_id=3
        And there is no tier deployment with deployment_id=3,environment_id=1
        And there is no host deployment with deployment_id=3,host_id=1
        And there is no host deployment with deployment_id=3,host_id=2

    Scenario: promote older version to all apptypes
        Given there is a deploy target with name="another-apptype"
        And there is a host with name="anotherhost01"
        And the host is associated with the deploy target
        And the tier "another-apptype" is associated with the application "myapp" for the project "proj"
        And the package "121" is deployed on the deploy targets in the "dev" env
        And the package "121" has been validated in the "development" environment
        When I run "deploy promote myapp 121 --all-apptypes --detach"
        Then the output has "Deployment ready for installer daemon, disconnecting now."
        And there is a deployment with status="queued",delay=0
        And there is a tier deployment with status="pending",deployment_id=4,app_id=2,package_id=1,environment_id=2
        And there is a tier deployment with status="pending",deployment_id=4,app_id=3,package_id=1,environment_id=2

    #TODO: Figure out whether to keep these tests and where to put them
    # Scenario: promote version to hosts with a failure
    #     Given the host "sprojhost01" will fail to deploy
    #     When I run "deploy promote myapp 123 --hosts sprojhost01 sprojhost02 --detach"
    #     Then the output has "Some hosts had failures"
    #     And the output has "Hostname: sprojhost01"
    #
    # Scenario: promote version to apptype with a failure
    #     Given the host "sprojhost01" will fail to deploy
    #     When I run "deploy promote myapp 123 --apptype the-apptype --detach"
    #     Then the output has "Some hosts had failures"
    #     And the output has "Hostname: sprojhost01"
    #
    # Scenario: promote version to all apptypes with a failure
    #     Given the host "sprojhost01" will fail to deploy
    #     When I run "deploy promote myapp 123 --all-apptypes --detach"
    #     Then the output has "Some hosts had failures"
    #     And the output has "Hostname: sprojhost01"

    Scenario: promote version to all apptypes with delay option
        When I run "deploy promote myapp 123 --delay 10 --detach"
        Then the output has "Deployment ready for installer daemon, disconnecting now."
        And there is a deployment with id=3,status="queued",delay=10
        And there is a tier deployment with deployment_id=3,status="pending",app_id=2,package_id=3,environment_id=2

    Scenario Outline: promote version that isn't validated in previous env with force option
        Given there is a package with version="124"
        When I run "deploy promote <switch> myapp 124 --detach"
        Then the output has "Deployment ready for installer daemon, disconnecting now."
        And there is a deployment with status="queued",delay=0
        And there is a tier deployment with status="pending",deployment_id=3,app_id=2,package_id=4,environment_id=2

        Examples:
            | switch    |
            | -f        |
            | --force   |

    Scenario: promote a version that has already been deployed
        Given the package is deployed on the deploy targets in the "stage" env
        When I run "deploy promote myapp 123 --detach"
        Then the output has "Application "myapp", version "123" is currently deployed on tier "the-apptype", skipping..."

    Scenario: promote a version that has already been validated
        Given the package is deployed on the deploy targets in the "stage" env
        And the package has been validated in the "staging" environment
        When I run "deploy promote myapp 123 --detach"
        Then the output has "Application "myapp", version "123" is currently deployed on tier "the-apptype", skipping..."

    Scenario: deploying to multiple hosts of different apptypes
        Given there is a deploy target with name="other-apptype"
        And there are hosts:
            | name       | env    |
            | dother01   | dev    |
            | dother02   | dev    |
            | sother01   | stage  |
            | sother02   | stage  |
        And the hosts are associated with the deploy target
        And the deploy target is a part of the project-application pair
        And there is a package with version="124"
        And the package is deployed on the deploy targets in the "dev" env
        And the package has been validated in the "development" environment
        When I run "deploy promote myapp 124 --hosts sprojhost01 sprojhost02 sother01 --detach"
        Then the output has "Deployment ready for installer daemon, disconnecting now."
        And there is a deployment with status="queued",delay=0
        And there is a host deployment with status="pending",deployment_id=4,host_id=3,package_id=4
        And there is a host deployment with status="pending",deployment_id=4,host_id=4,package_id=4
        And there is a host deployment with status="pending",deployment_id=4,host_id=7,package_id=4

    Scenario: deploying older version to multiple hosts of different apptypes
        Given there is a deploy target with name="other-apptype"
        And there are hosts:
            | name       | env    |
            | dother01   | dev    |
            | dother02   | dev    |
            | sother01   | stage  |
            | sother02   | stage  |
        And the hosts are associated with the deploy target
        And the deploy target is a part of the project-application pair
        And the package "121" is deployed on the deploy targets in the "dev" env
        And the package "121" has been validated in the "development" environment
        When I run "deploy promote myapp 121 --hosts sprojhost01 sprojhost02 sother01 --detach"
        Then the output has "Deployment ready for installer daemon, disconnecting now."
        And there is a deployment with status="queued",delay=0
        And there is a host deployment with status="pending",deployment_id=4,host_id=3,package_id=1
        And there is a host deployment with status="pending",deployment_id=4,host_id=4,package_id=1
        And there is a host deployment with status="pending",deployment_id=4,host_id=7,package_id=1
