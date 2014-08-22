Feature: package add subcommand
    As a user
    I want to add a specific version of a package
    So I can deploy that version of that package to targets

    Background:
        Given I have "dev" permissions
        And I am in the "dev" environment

    @no_db
    Scenario: too few arguments
        When I run "package add proj"
        Then the output has "usage:"

    @no_db
    Scenario: too many arguments
        When I run "package add proj vers foo"
        Then the output has "usage:"

    Scenario: add a package to a project that doesn't exist
        When I run "package add proj 123"
        Then the output has "Project "proj" does not exist"

    Scenario: add a package to a project with a version that doesn't exist
        Given there is a project with name="proj"
        When I run "package add proj 123"
        Then the output has "Package "proj-name@123" does not exist"

    Scenario: add a package to a project
        Given there is a project with name="proj"
        And there is an RPM package with name="proj-name",version="123",path="proj-path"
        When I start to run "package add proj 123"
        And I wait 10 seconds
        And the status is changed to "completed" for package version with name="proj-name",version=123
        And the command finishes
        Then the output has "Added package version: "proj-name@123""

    Scenario: add a package to a project again
        Given there is a project with name="proj"
        And there is a package version with version="123"
        When I run "package add proj 123"
        Then the output has "Package version "proj-name@123" already exists"
