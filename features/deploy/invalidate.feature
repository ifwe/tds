Feature: deploy invalidate application version [--apptypes|--all-apptypes]
    As a user
    I want to invalidate a package on deploy targets
    So I can prevent the package from being redeployed

    Background:
        Given I have "dev" permissions
        And there is an environment with name="dev"
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

    #Scenario: invalidate a package from an application with no hosts associated
    #    Given there is a deploy target with name="foo"
    #    And the deploy target is a part of the project-application pair
    #    And the package is deployed on the deploy target
    #    When I run "deploy invalidate myapp 123 --apptype foo"
    #    Then the output is "No hosts are associated with the app tier 'foo' in the dev environment"

    Scenario: invalidate a package from an application for an apptype with it currently deployed
        Given there is a deploy target with name="foo"
        And there are hosts:
            | name      |
            | dhost01   |
            | dhost02   |
        And the hosts are associated with the deploy target
        And the deploy target is a part of the project-application pair
        And the package is deployed on the deploy target
        When I run "deploy invalidate myapp 123 --apptype foo"
        Then the output is "Application "myapp", version "123" is currently deployed on tier "foo", skipping..."

    Scenario: invalidate a package from an application with single apptype
        Given there is a deploy target with name="foo"
        And there are hosts:
            | name      |
            | dhost01   |
            | dhost02   |
        And the hosts are associated with the deploy target
        And the deploy target is a part of the project-application pair
        And the package is deployed on the deploy target
        And the package has been validated
        And I wait 2 seconds
        And there is a package with version="124"
        And the package is deployed on the deploy target
        When I run "deploy invalidate myapp 123"
        Then the output is empty
        And the package version "123" is invalidated

    Scenario: invalidate a package from an application with single apptype with apptype option
        Given there is a deploy target with name="foo"
        And there are hosts:
            | name      |
            | dhost01   |
            | dhost02   |
        And the hosts are associated with the deploy target
        And the deploy target is a part of the project-application pair
        And the package is deployed on the deploy target
        And the package has been validated
        And I wait 2 seconds
        And there is a package with version="124"
        And the package is deployed on the deploy target
        When I run "deploy invalidate myapp 123 --apptype foo"
        Then the output is empty
        And the package version "123" is invalidated

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
            | bar   |
            | foo   |
        And there are hosts:
            | name      |
            | dhost01   |
            | dhost02   |
        And the hosts are associated with the deploy target
        And the deploy targets are a part of the project-application pair
        And the package is deployed on the deploy targets
        And the package has been validated
        And I wait 2 seconds
        And there is a package with version="124"
        And the package is deployed on the deploy target
        When I run "deploy invalidate myapp 123 --apptype foo"
        Then the output is empty
        And the package version "123" is invalidated for deploy target with name="foo"

    Scenario: invalidate a package from an application with multiple apptypes with all-apptypes option
        Given there is a deploy target with name="foo"
        And there are hosts:
            | name      |
            | dfoo01    |
            | dfoo02    |
        And the hosts are associated with the deploy target
        And there is a deploy target with name="bar"
        And there is a host with name="dbar01"
        And the host is associated with the deploy target
        And there is a host with name="dbar02"
        And the host is associated with the deploy target
        And the deploy targets are a part of the project-application pair
        And the package is deployed on the deploy targets
        And the package has been validated
        And I wait 2 seconds
        And there is a package with version="124"
        And the package is deployed on the deploy targets
        When I run "deploy invalidate myapp 123 --all-apptypes"
        Then the package version "123" is invalidated for deploy targets:
            | name  |
            | foo   |
            | bar   |
