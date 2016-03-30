Feature: deploy validate application version [-f|--force] [--apptypes|--all-apptypes]
    As a user
    I want to validate a package on deploy targets
    So I can allow the package to be deployed to the next environment and be redeployed

    Background:
        Given I have "dev" permissions
        And there is an environment with name="dev"
        And I am in the "dev" environment
        And there is a project with name="proj"
        And there is an application with name="myapp"
        And there is a deploy target with name="foo"
        And there is a package with version="123"
        And there are hosts:
            | name          |
            | projhost01    |
            | projhost02    |
        And the deploy target is a part of the project-application pair
        And the hosts are associated with the deploy target
        And the package is deployed on the deploy target

    Scenario: too few arguments
        When I run "deploy validate myapp"
        Then the output has "usage:"

    Scenario: too many arguments
        When I run "deploy validate myapp vers foo"
        Then the output has "usage:"

    Scenario: validate a package from an application that doesn't exist
        When I run "deploy validate badapp 123"
        Then the output is "Application does not exist: badapp"

    Scenario: validate a package from an application with a version that doesn't exist
        When I run "deploy validate myapp 124"
        Then the output is "Package does not exist: myapp@124"

    Scenario: validate a package from an application for an apptype that doesn't exist
        When I run "deploy validate myapp 123 --apptype bar"
        Then the output is "Valid apptypes for application "myapp" are: ['foo']"

    Scenario: validate a package from an application with one of several apptypes that doesn't exist
        When I run "deploy validate myapp 123 --apptype foo bar"
        Then the output is "Valid apptypes for application "myapp" are: ['foo']"

    Scenario: validate a package from an application for an apptype with it not currently deployed
        Given there is a deploy target with name="bar"
        And there are hosts:
            | name           |
            | anotherhost01  |
            | anotherhost02  |
        And the deploy target is a part of the project-application pair
        And the hosts are associated with the deploy target
        When I run "deploy validate myapp 123 --apptype bar"
        Then the output is "Tier "bar" has no current deployment for application "myapp", version "123" to validate"

    Scenario: validate a package from an application for an apptype with the deployment in progress
        Given there is a deploy target with name="bar"
        And there are hosts:
            | name           |
            | anotherhost01  |
            | anotherhost02  |
        And the deploy target is a part of the project-application pair
        And the hosts are associated with the deploy target
        And there is an ongoing deployment on the deploy target
        When I run "deploy validate myapp 123 --apptype bar"
        Then the output is "Tier "bar" has a current deployment that is in progress, skipping..."

    Scenario: validate a package from an application for an apptype with the deployment in invalidated state
        Given the package has been invalidated
        When I run "deploy validate myapp 123 --apptype foo"
        Then the output is "Application "myapp", version "123" has been validated on tier "foo""
        And the package is validated

    Scenario: validate a package from an application for an apptype with the deployment already validated
        Given the package has been validated
        When I run "deploy validate myapp 123 --apptype foo"
        Then the output is "Tier "foo" has a current deployment that is already validated, skipping..."

    Scenario: validate a package from an application for an apptype with the deployment in incomplete state
        Given the package failed to deploy on the host with name="projhost02"
        When I run "deploy validate myapp 123 --apptype foo"
        Then the output is "Tier "foo" has a current deployment that is incomplete, please use "--force" option to override"

    Scenario: validate a package from an application for an apptype with the deployment in incomplete state with force option
        Given the package failed to deploy on the host with name="projhost02"
        When I run "deploy validate myapp 123 --apptype foo --force"
        Then the output is "Application "myapp", version "123" has been validated on tier "foo""
        And the package is validated

    Scenario: validate a package from an application with single apptype
        When I run "deploy validate myapp 123"
        Then the output is "Application "myapp", version "123" has been validated on tier "foo""
        And the package is validated

    Scenario: validate a package from an application with single apptype with apptype option
        When I run "deploy validate myapp 123 --apptype foo"
        Then the output is "Application "myapp", version "123" has been validated on tier "foo""
        Then the package is validated

    Scenario: validate a package from an application with multiple apptypes with no options
        Given there is a deploy target with name="bar"
        And there are hosts:
            | name           | env  |
            | anotherhost01  | dev  |
            | anotherhost02  | dev  |
        And the deploy target is a part of the project-application pair
        And the hosts are associated with the deploy target
        And the package is deployed on the deploy target
        When I run "deploy validate myapp 123"
        Then the output is "Specify a target constraint (too many targets found: bar, foo)"

    Scenario: validate a package from an application with multiple apptypes with apptype option
        Given there is a deploy target with name="bar"
        And there is a host with name="anotherhost01",env="dev"
        And the host is associated with the deploy target
        And there is a host with name="anotherhost02",env="dev"
        And the host is associated with the deploy target
        And the deploy target is a part of the project-application pair
        And the package is deployed on the deploy target
        When I run "deploy validate myapp 123 --apptype foo"
        Then the output is "Application "myapp", version "123" has been validated on tier "foo""
        Then the package is validated for deploy target with name="foo"

    Scenario: validate a package from an application with multiple apptypes with all-apptypes option
        Given there is a deploy target with name="bar"
        And there is a host with name="anotherhost01",env="dev"
        And the host is associated with the deploy target
        And there is a host with name="anotherhost02",env="dev"
        And the host is associated with the deploy target
        And the deploy target is a part of the project-application pair
        And the package is deployed on the deploy target
        When I run "deploy validate myapp 123 --all-apptypes"
        Then the package is validated for the deploy targets
