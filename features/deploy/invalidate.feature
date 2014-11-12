Feature: deploy invalidate application version [--apptypes|--all-apptypes]
    As a user
    I want to invalidate a package on deploy targets
    So I can prevent the package from being redeployed

    Background:
        Given I have "dev" permissions
        And I am in the "dev" environment
        And there is a project with name="proj"
        And there is an application with name="myapp"
        And there is a package with version="123"

    Scenario: too few arguments
        When I run "deploy invalidate myapp"
        Then the output has "usage:"

    Scenario: too many arguments
        When I run "deploy invalidate myapp vers foo"
        Then the output has "usage:"

    Scenario: invalidate a package from an application that does not exist
        When I run "deploy invalidate badapp 567 --all-apptypes"
        Then the output is "Application does not exist: badapp"

    Scenario: invalidate a package from an application with a version that does not exist
        When I run "deploy invalidate myapp 124 --all-apptypes"
        Then the output is "Package does not exist: myapp@124"

    Scenario: invalidate a package from an application for an apptype that does not exist
        When I run "deploy invalidate myapp 123 --apptype foo"
        Then the output is "Valid apptypes for application "myapp" are: []"

    Scenario: invalidate a package from an application with one of several apptypes that does not exist
        Given there is a deploy target with name="foo"
        And the deploy target is a part of the project-application pair
        When I run "deploy invalidate myapp 123 --apptype foo bar"
        Then the output is "Valid apptypes for application "myapp" are: ['foo']"

    Scenario: invalidate a package from an application for an apptype with it currently deployed
        Given there is a deploy target with name="foo"
        And the deploy target is a part of the project-application pair
        And the package is deployed on the deploy target
        When I run "deploy invalidate myapp 123 --apptype foo"
        Then the output is "Package "myapp@123" currently deployed on target "foo""

    Scenario: invalidate a package from an application for an apptype
        Given there is a deploy target with name="foo"
        And the deploy target is a part of the project-application pair
        And the package is deployed on the deploy target
        When I run "deploy invalidate myapp 123 --apptype foo"
        Then the output is "Package "myapp@123" currently deployed on target "foo""

    Scenario: invalidate a package from an application with single apptype
        Given there is a deploy target with name="foo"
        And the deploy target is a part of the project-application pair
        And the package is deployed on the deploy target
        And the package has been validated
        When I run "deploy invalidate myapp 123"
        Then the output is empty
        Then the package is invalidated

    Scenario: invalidate a package from an application with single apptype with apptype option
        Given there is a deploy target with name="foo"
        And the deploy target is a part of the project-application pair
        And the package is deployed on the deploy target
        And the package has been validated
        When I run "deploy invalidate myapp 123 --apptype foo"
        Then the package is invalidated

    Scenario: invalidate a package from an application with multiple apptypes with no options
        Given there are deploy targets:
            | name  |
            | foo   |
            | bar   |
        And the deploy targets are a part of the project-application pair
        And the package is deployed on the deploy targets
        And the package has been validated
        When I run "deploy invalidate myapp 123"
        Then the output is "Specify a target constraint (too many targets found: bar, foo)"

    Scenario: invalidate a package from an application with multiple apptypes with apptype option
        Given there are deploy targets:
            | name  |
            | foo   |
            | bar   |
        And the deploy targets are a part of the project-application pair
        And the package is deployed on the deploy targets
        And the package has been validated
        When I run "deploy invalidate myapp 123 --apptype foo"
        Then the package is invalidated for deploy target with name="foo"

    Scenario: invalidate a package from an application with multiple apptypes with all-apptypes option
        Given there are deploy targets:
            | name  |
            | foo   |
            | bar   |
        And the deploy targets are a part of the project-application pair
        And the package is deployed on the deploy targets
        And the package has been validated
        When I run "deploy invalidate myapp 123 --all-apptypes"
        Then the package is invalidated for deploy targets:
            | name  |
            | foo   |
            | bar   |
