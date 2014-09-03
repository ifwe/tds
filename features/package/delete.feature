Feature: package delete subcommand
    As a user
    I want to remove a specific version of a package
    So I can no longer deploy that version of that package to targets

    Background:
        Given I have "dev" permissions
        And I am in the "dev" environment

    @no_db
    Scenario: too few arguments
        When I run "package delete proj"
        Then the output has "usage:"

    @no_db
    Scenario: too many arguments
        When I run "package delete proj vers foo"
        Then the output has "usage:"

    Scenario: delete a package from a project that doesn't exist
        When I run "package delete proj 123"
        Then the output is "Project "proj" does not exist"

    Scenario: delete a package from a project with a version that doesn't exist
        Given there is a project with name="proj"
        When I run "package delete proj 123"
        Then the output is "Package "proj-name@123" does not exist"

    Scenario: delete a package from a project
        Given there is a project with name="proj"
        And there is a package version with version="123"
        When I run "package delete proj 123"
        Then the output is "This command is not implemented yet"

    Scenario: Delete a target from a project again
        Given there is a project with name="proj"
        And there is a package version with version="123"
        When I run "package delete proj 123"
        Then the output is "This command is not implemented yet"
