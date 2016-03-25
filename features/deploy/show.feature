Feature: deploy show application version [--apptypes] [--all-apptypes]
    As a user
    I want to show deployed targets to applications
    So I can determine the state of the deployments to the applications

    Background:
        Given I have "dev" permissions
        And there is an environment with name="dev"
        And I am in the "dev" environment
        And there is a project with name="proj"
        And there is an application with name="myapp"
        And there is a deploy target with name="foo"
        And the deploy target is a part of the project-application pair
        And there are hosts:
            | name          | env   |
            | projhost01    | dev   |
            | projhost02    | dev   |
        And the hosts are associated with the deploy target
        And there is a package with version="123"

    Scenario: too few arguments
        When I run "deploy show"
        Then the output has "usage:"

    Scenario: too many arguments
        When I run "deploy show myapp 123 foo"
        Then the output has "usage:"

    Scenario: with a project that doesn't exist
        When I run "deploy show badapp"
        Then the output is "Application does not exist: badapp"

    Scenario: with a application and a version that doesn't exist
        When I run "deploy show myapp 123"
        Then the output describes no deployments

    Scenario: with a application and an apptype that doesn't exist
        When I run "deploy show myapp --apptypes bar"
        Then the output is "Valid apptypes for application "myapp" are: ['foo']"

    Scenario: with a application and an apptype and a version that doesn't exist
        When I run "deploy show myapp 124 --apptypes foo"
        Then the output is "Package does not exist: myapp@124"

    Scenario: with --apptypes and --all-apptypes
        When I run "deploy show myapp 123 --all-apptypes --apptypes foo"
        Then the output is "These options are exclusive: hosts, apptypes, all-apptypes"

    Scenario: with a application and a version for a tier
        Given the package is deployed on the deploy target
        And the package has been validated
        When I run "deploy show myapp 123"
        Then the output describes the app deployments

    Scenario: with a application and an apptype
        Given the package is deployed on the deploy target
        And the package has been validated
        When I run "deploy show myapp --apptypes foo"
        Then the output describes the app deployments

    Scenario: with a application and a version and an apptype
        Given the package is deployed on the deploy target
        And the package has been validated
        When I run "deploy show myapp 123 --apptypes foo"
        Then the output describes the app deployments

    Scenario: without package validation
        Given the package is deployed on the deploy target
        When I run "deploy show myapp 123 --apptypes foo"
        Then the output describes the app deployments
        And the output describes the host deployments

    Scenario: host-only deployments with all-apptypes
        Given the package is deployed on the hosts
        When I run "deploy show myapp 123 --all-apptypes"
        Then the output describes the host deployments

    Scenario: host-only deployments with specific apptype
        Given the package is deployed on the hosts
        When I run "deploy show myapp 123 --apptypes foo"
        Then the output describes the host deployments

    Scenario: with a different version deployed to hosts
        Given the package is deployed on the deploy target
        And there is a package with version="200"
        And the package is deployed on the hosts
        When I run "deploy show myapp --apptypes foo"
        Then the output describes the host deployments
        And the output describes an app deployment with version="123"

    Scenario: check host output for different deployment to hosts
        Given the package is deployed on the deploy target
        And there is a package with version="200"
        And the package is deployed on the hosts
        When I run "deploy show myapp 200 --apptypes foo"
        Then the output describes the host deployments

    Scenario: check app output for different deployment to hosts
        Given the package is deployed on the deploy target
        And there is a package with version="200"
        And the package is deployed on the hosts
        When I run "deploy show myapp 123 --apptypes foo"
        Then the output describes an app deployment with version="123"
        And the output does not describe a host deployment with name="myapp"

    Scenario: different version deployed to only one host
        Given the package is deployed on the deploy target
        And there is a package with version="200"
        And the package is deployed on the host with name="projhost01"
        When I run "deploy show myapp 200 --apptypes foo"
        Then the output describes a host deployment with name="myapp",host_name="projhost01"
        And the output does not describe a host deployment with host_name="projhost02"

    Scenario: check app output with different version deployed to only one host
        Given the package is deployed on the deploy target
        And there is a package with version="200"
        And the package is deployed on the host with name="projhost01"
        When I run "deploy show myapp 123 --apptypes foo"
        Then the output describes a host deployment with name="myapp",host_name="projhost02"
        And the output describes an app deployment with name="myapp"
        And the output does not describe a host deployment with host_name="projhost01"

    Scenario: different versions with validation
        Given the package is deployed on the deploy target
        And the package has been validated
        And there is a package with version="200"
        And the package is deployed on the host with name="projhost01"
        When I run "deploy show myapp 123 --apptypes foo"
        Then the output describes an app deployment with name="myapp",version="123"
        And the output does not describe a host deployment with name="myapp"

    Scenario: host output with different version with validation
        Given the package is deployed on the deploy target
        And the package has been validated
        And there is a package with version="200"
        And the package is deployed on the host with name="projhost01"
        When I run "deploy show myapp 200 --apptypes foo"
        Then the output describes a host deployment with name="myapp",host_name="projhost01"
        And the output does not describe a host deployment with host_name="projhost02"

    Scenario: with multiple apptypes without all-apptypes used
        Given there is a deploy target with name="bar"
        And the deploy target is a part of the project-application pair
        And there are hosts:
            | name          | env   |
            | otherhost01   | dev   |
            | otherhost02   | dev   |
        And the hosts are associated with the deploy target
        And the package is deployed on the deploy target
        And the package is validated
        When I run "deploy show myapp"
        Then the output is "Specify a target constraint (too many targets found: bar, foo)"

    Scenario: with multiple apptypes with all-apptypes and different versions
        Given the package is deployed on the deploy target
        And the package has been validated
        And there is a deploy target with name="bar"
        And the deploy target is a part of the project-application pair
        And there are hosts:
            | name          | env   |
            | otherhost01   | dev   |
            | otherhost02   | dev   |
        And the hosts are associated with the deploy target
        And there is a package with version="200"
        And the package is deployed on the deploy target
        And the package is validated
        When I run "deploy show myapp --all-apptypes"
        Then the output describes an app deployment with version="123"
        And the output describes an app deployment with version="200"

    Scenario: with the current version as the most recently validated version
        Given the package is deployed on the deploy target
        And the package has been validated
        And there is a package with version="124"
        And the package is deployed on the deploy target
        And the package has been validated
        And there is a deploy target with name="bar"
        And the deploy target is a part of the project-application pair
        And there are hosts:
            | name          | env   | app_id    |
            | otherhost01   | dev   | 3         |
            | otherhost02   | dev   | 3         |
        And there is a package with version="200"
        And the package is deployed on the deploy target
        And the package is validated
        And there is a package with version="201"
        And the package is deployed on the deploy target
        And the package is validated
        When I run "deploy show myapp --all-apptypes"
        Then the output describes an app deployment with version="124"
        And the output has "Rollback deployment version:"
        And the output describes an app deployment with version="123"
        And the output describes an app deployment with version="200"
        And the output describes an app deployment with version="201"

    Scenario: with the current version as incomplete
        Given the package is deployed on the deploy target
        And the package has been validated
        And there is a package with version="124"
        And the package is deployed on the deploy target
        And the package has been validated
        And there is a deploy target with name="bar"
        And the deploy target is a part of the project-application pair
        And the package is deployed on the deploy target
        And the package is validated
        And I wait 1 seconds
        And there are hosts:
            | name          | env   | app_id    |
            | otherhost01   | dev   | 3         |
            | otherhost02   | dev   | 3         |
        And there is a package with version="200"
        And the package is deployed on the deploy target
        And the package is validated
        And I wait 1 seconds
        And there is a package with version="201"
        And there are deployments:
            | id    | user  | status    |
            | 2     | foo   | failed    |
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status        | user  | app_id    | package_id    |
            | 5     | 2             | 1                 | incomplete    | foo   | 3         | 4             |
        And there are host deployments:
            | id    | deployment_id | status    | user  | host_id   | package_id    |
            | 7     | 2             | ok        | foo   | 3         | 4             |
            | 8     | 2             | failed    | foo   | 4         | 4             |
        When I run "deploy show myapp --apptypes bar"
        Then the output has "Rollback deployment version:"
        And the output describes an app deployment with version="201"

    Scenario: with the most recent deployment invalidated
        Given the package is deployed on the deploy target
        And the package has been validated
        And there is a package with version="124"
        And the package is deployed on the deploy target
        And the package has been validated
        And there is a deploy target with name="bar"
        And the deploy target is a part of the project-application pair
        And there are hosts:
            | name          | env   | app_id    |
            | otherhost01   | dev   | 3         |
            | otherhost02   | dev   | 3         |
        And there is a package with version="200"
        And the package is deployed on the deploy target
        And the package is validated
        And there is a package with version="201"
        And the package is deployed on the deploy target
        And the package is invalidated
        When I run "deploy show myapp --all-apptypes"
        Then the output describes an app deployment with version="124"
        And the output has "Rollback deployment version:"
        And the output describes an app deployment with version="123"
        And the output describes an app deployment with version="200"
