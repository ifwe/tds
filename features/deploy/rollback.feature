Feature: deploy rollback application [--delay] [--hosts|--apptypes|--all-apptypes] [--detach]
    As a developer
    I want to redeploy older versions of applications to targets
    So that I can correct problems with services easily

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
            | name          | env   |
            | projhost01    | stage |
            | projhost02    | stage |
        And the hosts are associated with the deploy target

        And there is a package with version="121"
        And the package is deployed on the deploy target
        And the package has been validated

        And I wait 1 seconds
        And there is a package with version="122"
        And the package is deployed on the deploy target
        And the package has been invalidated

        And I wait 1 seconds
        And there is a package with version="123"
        And the package is deployed on the deploy target
        And the package has been validated

    Scenario: rollback application that doesn't exist
        When I run "deploy rollback badapp --detach"
        Then the output has "Application does not exist: badapp"

    Scenario: rollback version to host that doesn't exist
        When I run "deploy rollback myapp --hosts badhost01 --detach"
        Then the output has "Host does not exist: badhost01"

    Scenario: rollback version to apptype that doesn't exist
        When I run "deploy rollback myapp --apptype bad-apptype --detach"
        Then the output has "Valid apptypes for application "myapp" are: ['the-apptype']"

    Scenario: rollback command with no specifier
        When I run "deploy rollback myapp --detach"
        Then the output has "Deployment ready for installer daemon, disconnecting now."
        And there is a deployment with id=2,status="queued",delay=0
        And there is a tier deployment with deployment_id=2,app_id=2,status="pending",environment_id=2,package_id=1
        And there is a host deployment with deployment_id=2,host_id=1,status="pending",package_id=1
        And there is a host deployment with deployment_id=2,host_id=2,status="pending",package_id=1
        And there is a tier deployment with app_id=2,status="invalidated",environment_id=2,package_id=3

    Scenario: rollback version to hosts
        Given there is a package with version="124"
        And the package is deployed on the hosts
        When I run "deploy rollback myapp --hosts projhost01 projhost02 --detach"
        Then the output has "Deployment ready for installer daemon, disconnecting now."
        And there is a deployment with id=2,status="queued",delay=0
        And there is a host deployment with deployment_id=2,host_id=1,status="pending",package_id=3
        And there is a host deployment with deployment_id=2,host_id=2,status="pending",package_id=3
        And there is no tier deployment with deployment_id=2,app_id=2
        And there is no tier deployment with app_id=2,status="invalidated",environment_id=2,package_id=3

    Scenario: rollback version to one host out of tier
        Given there is a package with version="124"
        And the package is deployed on the hosts
        When I run "deploy rollback myapp --hosts projhost01 --detach"
        Then the output has "Deployment ready for installer daemon, disconnecting now."
        And there is a deployment with id=2,status="queued",delay=0
        And there is a host deployment with deployment_id=2,host_id=1,status="pending",package_id=3
        And there is no host deployment with deployment_id=2,host_id=2
        And there is no tier deployment with deployment_id=2,app_id=2
        And there is no tier deployment with app_id=2,status="invalidated",environment_id=2,package_id=3

    Scenario: rollback version to apptype
        When I run "deploy rollback myapp --apptype the-apptype --detach"
        Then the output has "Deployment ready for installer daemon, disconnecting now."
        And there is a deployment with id=2,status="queued",delay=0
        And there is a tier deployment with deployment_id=2,app_id=2,status="pending",environment_id=2,package_id=1
        And there is a host deployment with deployment_id=2,host_id=1,status="pending",package_id=1
        And there is a host deployment with deployment_id=2,host_id=2,status="pending",package_id=1
        And there is a tier deployment with app_id=2,status="invalidated",environment_id=2,package_id=3
        And there is no host deployment with deployment_id=1

    Scenario: rollback version to all apptypes
        Given there is a deploy target with name="another-apptype"
        And the deploy target is a part of the project-application pair
        And there is a host with name="anotherhost01"
        And the host is associated with the deploy target

        And the package "121" is deployed on the deploy target
        And the package "121" is validated

        And I wait 1 seconds
        And the package "122" is deployed on the deploy target
        And the package "122" is invalidated

        And I wait 1 seconds
        And the package "123" is deployed on the deploy target
        And the package "123" is validated

        When I run "deploy rollback myapp --all-apptypes --detach"
        Then the output has "Deployment ready for installer daemon, disconnecting now."
        And there is a deployment with id=2,status="queued",delay=0
        And there is a tier deployment with deployment_id=2,app_id=2,status="pending",environment_id=2,package_id=1
        And there is a tier deployment with deployment_id=2,app_id=3,status="pending",environment_id=2,package_id=1
        And there is a tier deployment with deployment_id=1,app_id=2,status="invalidated",environment_id=2,package_id=2
        And there is a tier deployment with deployment_id=1,app_id=3,status="invalidated",environment_id=2,package_id=2
        And there is no host deployment with deployment_id=1
        And there is a host deployment with deployment_id=2,host_id=1,status="pending",package_id=1
        And there is a host deployment with deployment_id=2,host_id=2,status="pending",package_id=1
        And there is a tier deployment with app_id=2,status="invalidated",environment_id=2,package_id=3
        And there is a tier deployment with app_id=3,status="invalidated",environment_id=2,package_id=3

    #TODO: Figure out what to do with these tests
    # Scenario: rollback version to hosts with a failure
    #     Given the host "projhost01" will fail to deploy
    #     When I run "deploy rollback myapp --hosts projhost01 projhost02 --detach"
    #     Then the output has "Some hosts had failures"
    #     And the output has "Hostname: projhost01"
    #
    # Scenario: rollback version to apptype with a failure
    #     Given the host "projhost01" will fail to deploy
    #     When I run "deploy rollback myapp --apptype the-apptype --detach"
    #     Then the output has "Some hosts had failures"
    #     And the output has "Hostname: projhost01"
    #
    # Scenario: rollback version to all apptypes with a failure
    #     Given there is a deploy target with name="another-apptype"
    #     And the deploy target is a part of the project-application pair
    #     And there is a host with name="anotherhost01"
    #     And the host is associated with the deploy target
    #
    #     And the package "121" is deployed on the deploy target
    #     And the package has been validated
    #
    #     And I wait 1 seconds
    #     And the package "122" is deployed on the deploy target
    #     And the package has been invalidated
    #
    #     And I wait 1 seconds
    #     And the package "123" is deployed on the deploy target
    #     And the package has been validated
    #
    #     And the host "projhost01" will fail to deploy
    #     When I run "deploy rollback myapp --all-apptypes --detach"
    #     Then the output has "Some hosts had failures"
    #     And the output has "Hostname: projhost01"

    Scenario: rollback a single host out of multiple apptypes
        Given there is a deploy target with name="another-apptype"
        And the deploy target is a part of the project-application pair
        And there is a host with name="anotherhost01"
        And the host is associated with the deploy target
        And there is a host with name="anotherhost02"
        And the host is associated with the deploy target

        And the package "121" is deployed on the deploy target
        And the package has been validated

        And I wait 1 seconds
        And the package "122" is deployed on the deploy target
        And the package has been validated

        And I wait 1 seconds
        And the package "123" is deployed on the deploy target
        And the package has been validated

        And I wait 1 seconds
        And there is a package with version="124"
        And the package "124" is deployed on the deploy target
        And the package has been validated

        When I run "deploy rollback myapp --hosts anotherhost01 --detach"
        Then the output has "Deployment ready for installer daemon, disconnecting now."
        And there is a deployment with id=2,status="queued",delay=0
        And there is a host deployment with deployment_id=2,host_id=3,status="pending",package_id=3
        And there is no host deployment with deployment_id=2,host_id=1
        And there is no host deployment with deployment_id=2,host_id=2
        And there is no host deployment with deployment_id=2,host_id=4
        And there is no tier deployment with deployment_id=2,app_id=2
        And there is no tier deployment with deployment_id=2,app_id=3
        And there is no tier deployment with app_id=2,status="invalidated",environment_id=2,package_id=3
        And there is no tier deployment with app_id=3,status="invalidated",environment_id=2,package_id=4

    Scenario: rollback version with delay option
        When I run "deploy rollback myapp --delay 10 --detach"
        Then the output has "Deployment ready for installer daemon, disconnecting now."
        And there is a deployment with id=2,status="queued",delay=10
        And there is a tier deployment with deployment_id=2,app_id=2,status="pending",environment_id=2,package_id=1
        And there is a host deployment with deployment_id=2,host_id=1,status="pending",package_id=1
        And there is a host deployment with deployment_id=2,host_id=2,status="pending",package_id=1
        And there is a tier deployment with app_id=2,status="invalidated",environment_id=2,package_id=3

    Scenario: rollback on host with no validated deployment
        Given there is a deploy target with name="tier2"
        And the deploy target is a part of the project-application pair
        And there are hosts:
            | name  | env   | app_id    |
            | host1 | stage | 3         |
            | host2 | stage | 3         |
        And the package is deployed on the deploy target
        When I run "deploy rollback myapp --hosts host1 --detach"
        Then the output has "No validated tier deployment for application myapp on tier tier2 of host host1 before currently deployed version. Skipping..."
        And the output has "Nothing to do."
        And there is no deployment with id=2
        And there is no host deployment with deployment_id=2,host_id=3

    Scenario: rollback on host with no completed deployment
        Given there is a deploy target with name="tier2"
        And the deploy target is a part of the project-application pair
        And there are hosts:
            | name  | env   | app_id    |
            | host1 | stage | 3         |
            | host2 | stage | 3         |
        When I run "deploy rollback myapp --hosts host1 --detach"
        Then the output has "no deployed version found for host "host1""
        And there is no deployment with id=2
        And there is no host deployment with deployment_id=2,host_id=3

    Scenario: rollback on tier with no validated deployment
        Given there is a deploy target with name="tier2"
        And the deploy target is a part of the project-application pair
        And there are hosts:
            | name  | env   | app_id    |
            | host1 | stage | 3         |
            | host2 | stage | 3         |
        And the package is deployed on the deploy target
        When I run "deploy rollback myapp --apptypes tier2 --detach"
        Then the output has "No validated tier deployment for application myapp on tier tier2 before currently deployed version. Skipping..."
        And the output has "Nothing to do."
        And there is no deployment with id=2
        And there is no tier deployment with deployment_id=2,app_id=3

    Scenario: rollback on tier with no completed deployment
        Given there is a deploy target with name="tier2"
        And the deploy target is a part of the project-application pair
        And there are hosts:
            | name  | env   | app_id    |
            | host1 | stage | 3         |
            | host2 | stage | 3         |
        When I run "deploy rollback myapp --apptypes tier2 --detach"
        Then the output has "no deployed version found for target "tier2""
        And there is no deployment with id=2
        And there is no tier deployment with deployment_id=2,app_id=3
