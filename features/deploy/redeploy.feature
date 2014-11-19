Feature: deploy redeploy application [--delay] [--hosts|--apptypes|--all-apptypes]
    As a developer
    I want to redeploy failed deployments to targets
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
        And the deploy target is a part of the project-application pair
        And there are hosts:
            | name          | env     |
            | dprojhost01   | dev     |
            | dprojhost02   | dev     |
            | sprojhost01   | stage   |
            | sprojhost02   | stage   |
        And the hosts are associated with the deploy target

        And there is a package with version="122"
        And the package is deployed on the deploy targets in the "stage" env
        And the package has been validated in the "staging" environment

        And there is a package with version="123"
        And the package is deployed on the deploy targets in the "dev" env
        And the package has been validated in the "development" environment
        And the package is deployed on the deploy targets in the "stage" env
        And the package failed to deploy on the host with name="sprojhost02"

    Scenario: redeploy application that doesn't exist
        When I run "deploy redeploy badapp"
        Then the output has "Application does not exist: badapp"

    Scenario: redeploy to host that doesn't exist
        When I run "deploy redeploy myapp --hosts badhost01"
        Then the output has "Host does not exist: badhost01"

    Scenario: redeploy to apptype that doesn't exist
        When I run "deploy redeploy myapp --apptype bad-apptype"
        Then the output has "Valid apptypes for application "myapp" are: ['the-apptype']"

    Scenario: redeploy to hosts
        When I run "deploy redeploy myapp --hosts sprojhost02"
        Then the output has "Completed: 1 out of 1 hosts"
        And package "myapp" version "123" was deployed to host "sprojhost02"

    Scenario: redeploy to apptype
        When I run "deploy redeploy myapp --apptype the-apptype"
        Then the output has "Completed: 2 out of 2 hosts"
        And the output has "Host "sprojhost01" already has "myapp@123" successfully deployed, skipping"
        And package "myapp" version "123" was deployed to host "sprojhost02"

    Scenario: redeploy to all apptypes
        Given there is a deploy target with name="another-apptype"
        And there is a host with name="anotherhost01"
        And the host is associated with the deploy target
        And the deploy target is a part of the project-application pair
        And the package is deployed on the deploy target
        And the package failed to deploy on the host with name="anotherhost01"
        When I run "deploy redeploy myapp --all-apptypes"
        Then the output has "Completed: 2 out of 2 hosts"
        And the output has "Completed: 1 out of 1 hosts"
        And package "myapp" version "123" was deployed to host "sprojhost02"
        And package "myapp" version "123" was deployed to host "anotherhost01"

    Scenario: redeploy to host with a failure
        Given the host "sprojhost02" will fail to deploy
        When I run "deploy redeploy myapp --hosts sprojhost02"
        Then the output has "Some hosts had failures"
        And the output has "Hostname: sprojhost02"

    Scenario: redeploy to apptype with a failure
        Given the host "sprojhost02" will fail to deploy
        When I run "deploy redeploy myapp --apptype the-apptype"
        Then the output has "Some hosts had failures"
        And the output has "Hostname: sprojhost02"

    Scenario: redeploy to all apptypes with a failure
        Given the host "sprojhost02" will fail to deploy
        When I run "deploy redeploy myapp --all-apptypes"
        Then the output has "Some hosts had failures"
        And the output has "Hostname: sprojhost02"

    @delay
    Scenario: redeploy with delay option
        When I run "deploy redeploy myapp --delay 10"
        Then the output has "Completed: 2 out of 2 hosts"
        And package "myapp" version "123" was deployed to host "sprojhost02"
        And the output has "Host "sprojhost01" already has "myapp@123" successfully deployed, skipping"
        And it took at least 10 seconds
