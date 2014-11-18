Feature: application delete-apptype application project target(s)
    As an administrator
    I want to remove deploy targets from project/application pairs
    So I can stop deploying packages to the targets

    Background:
        Given I have "admin" permissions
        And there is an environment with name="dev"
        And I am in the "dev" environment
        And there is a project with name="proj"
        And there is an application with name="myapp"
        And there is a deploy target with name="targ1"
        And the deploy target is a part of the project-application pair

    # TODO: should these arg checks be in another file that checks overall
    #       cli behavior?
    Scenario: too few arguments
        When I run "application delete-apptype myapp proj"
        Then the output has "usage:"

    Scenario: delete a target from a project/application pair with an application that doesn't exist
        When I run "application delete-apptype badapp proj targ"
        Then the output is "Application does not exist: badapp"

    Scenario: delete a target from a project/application pair with a project that doesn't exist
        When I run "application delete-apptype myapp badproj targ"
        Then the output is "Project does not exist: badproj"

    Scenario: delete a target that doesn't exist from a project/application pair
        When I run "application delete-apptype myapp proj badtarg"
        Then the output is "Valid apptypes for application "myapp" are: ['targ1']"

    Scenario: delete a target from a project/application pair where target has no current active deployments
        When I run "application delete-apptype myapp proj targ1"
        Then the output is "Future deployments of "myapp" in "proj" will no longer affect "targ1""
        And the deploy target is not a part of the project-application pair

    Scenario: delete a target from a project/application pair where target has current active deployments (tier)
        Given there is a host with name="targ1host01"
        And the host is associated with the deploy target
        And there is a package with version="123"
        And the package is deployed on the deploy target
        When I run "application delete-apptype myapp proj targ1"
        Then the output is "Apptype "targ1" still has active deployments"
        And the deploy target is a part of the project-application pair

    Scenario: delete a target from a project/application pair where target has current active deployments (host)
        Given there is a host with name="targ1host01"
        And the host is associated with the deploy target
        And there is a package with version="123"
        And the package is deployed on the hosts
        When I run "application delete-apptype myapp proj targ1"
        Then the output is "Apptype "targ1" still has active deployments"
        And the deploy target is a part of the project-application pair

    # TODO: Lots of tests to write below this!
