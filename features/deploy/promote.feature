Feature: deploy promote application version [-f|--force] [--delay] [--hosts|--apptypes|--all-apptypes] (-f/--force only for deploy promote)
    As a developer
    I want to deploy applications to targets
    So that I can update services easily

    Background:
        Given I have "stage" permissions
        And I am in the "stage" environment
        And there is a project with name="proj"
        And there is an application with name="myapp"
        And there is a deploy target with name="the-apptype"
        And there is a package with version="123"
        And the package is deployed on the deploy targets in the "dev" env
        And the package has been validated in the "development" environment
        And there are hosts:
            | name          | env   |
            | dprojhost01   | dev   |
            | dprojhost02   | dev   |
            | sprojhost01   | stage |
            | sprojhost02   | stage |
        And the deploy target is a part of the project-application pair
        And the hosts are associated with the deploy target

    Scenario: promote application that doesn't exist
        When I run "deploy promote badapp 456"
        Then the output is "Application does not exist: badapp"

    Scenario: promote version that doesn't exist
        When I run "deploy promote myapp 456"
        Then the output is "Package does not exist: myapp@456"

    Scenario: promote version to host that doesn't exist
        When I run "deploy promote myapp 123 --hosts badhost01"
        Then the output has "Host does not exist: badhost01"

    Scenario: promote version to apptype that doesn't exist
        When I run "deploy promote myapp 123 --apptype bad-apptype"
        Then the output has "Valid apptypes for application "myapp" are: ['the-apptype']"

    Scenario: promote version to apptype that's not a part of the project
        Given there is a deploy target with name="other-apptype"
        When I run "deploy promote myapp 123 --apptype other-apptype"
        Then the output has "Valid apptypes for application "myapp" are: ['the-apptype']"

    Scenario: promote version that isn't validated in previous env (only for deploy)
        Given there is a package with version="124"
        When I run "deploy promote myapp 124"
        Then the output has "Package "myapp@124" never validated in "dev" environment for target "the-apptype""

    Scenario: promote version to hosts
        When I run "deploy promote myapp 123 --hosts sprojhost01 sprojhost02"
        Then the output has "Completed: 2 out of 2 hosts"
        And package "myapp" version "123" was deployed to these hosts:
            | name          |
            | sprojhost01   |
            | sprojhost02   |

    Scenario: promote version to apptype
        When I run "deploy promote myapp 123 --apptype the-apptype"
        Then the output has "Completed: 2 out of 2 hosts"
        And package "myapp" version "123" was deployed to the deploy target

    Scenario: promote version to all apptypes
        Given there is a deploy target with name="another-apptype"
        And there is a host with name="anotherhost01"
        And the host is associated with the deploy target
        And the deploy target is a part of the project-application pair
        And the package is deployed on the deploy targets in the "dev" env
        And the package has been validated in the "development" environment
        When I run "deploy promote myapp 123 --all-apptypes"
        Then the output has "Completed: 2 out of 2 hosts"
        And the output has "Completed: 1 out of 1 hosts"
        And package "myapp" version "123" was deployed to the deploy targets

    Scenario: promote version to hosts with a failure
        Given the host "sprojhost01" will fail to deploy
        When I run "deploy promote myapp 123 --hosts sprojhost01 sprojhost02"
        Then the output has "Some hosts had failures"
        And the output has "Hostname: sprojhost01"

    Scenario: promote version to apptype with a failure
        Given the host "sprojhost01" will fail to deploy
        When I run "deploy promote myapp 123 --apptype the-apptype"
        Then the output has "Some hosts had failures"
        And the output has "Hostname: sprojhost01"

    Scenario: promote version to all apptypes with a failure
        Given the host "sprojhost01" will fail to deploy
        When I run "deploy promote myapp 123 --all-apptypes"
        Then the output has "Some hosts had failures"
        And the output has "Hostname: sprojhost01"

    @delay
    Scenario: promote version to with delay option
        When I run "deploy promote myapp 123 --delay 10"
        Then the output has "Completed: 2 out of 2 hosts"
        And package "myapp" version "123" was deployed to the deploy target
        And it took at least 10 seconds

    Scenario Outline: promote version that isn't validated in previous env with force option
        Given there is a package with version="124"
        When I run "deploy promote <switch> myapp 124"
        Then the output has "Completed: 2 out of 2 hosts"
        And package "myapp" version "124" was deployed to the deploy target

        Examples:
            | switch    |
            | -f        |
            | --force   |

    Scenario: promote a version that has already been deployed
        Given the package is deployed on the deploy targets in the "stage" env
        When I run "deploy promote myapp 123"
        Then the output has "Application "myapp" with version "123" already deployed to this environment (staging) for apptype "the-apptype""

    Scenario: promote a version that has already been validated
        Given the package is deployed on the deploy targets in the "stage" env
        And the package has been validated in the "staging" environment
        When I run "deploy promote myapp 123"
        Then the output has "Application "myapp" with version "123" already deployed to this environment (staging) for apptype "the-apptype""

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
        When I run "deploy promote myapp 124 --hosts sprojhost01 sprojhost02 sother01"
        Then the output has "Completed: 3 out of 3 hosts"
        And package "myapp" version "124" was deployed to these hosts:
            | name          |
            | sprojhost01   |
            | sprojhost02   |
            | sother01      |
