Feature: package delete subcommand
    As a user
    I want to remove a specific version of a package
    So I can no longer deploy that version of that package to targets

    Background:
        Given I have "dev" permissions
        And there is an environment with name="dev"
        And I am in the "dev" environment

    @no_db
    Scenario: too few arguments
        When I run "package delete myapp"
        Then the output has "usage:"

    @no_db
    Scenario: too many arguments
        When I run "package delete myapp vers foo"
        Then the output has "usage:"

    Scenario: delete a package from an application that doesn't exist
        When I run "package delete myapp 123"
        Then the output is "Application does not exist: myapp"

    Scenario: delete a package from an application with a version that doesn't exist
        Given there is an application with name="myapp"
        When I run "package delete myapp 123"
        Then the output is "Package does not exist: myapp@123"

    Scenario: delete a package from an application
        Given there is an application with name="myapp"
        And there is a package with version="123"
        When I run "package delete myapp 123"
        Then the output is "This command is not implemented yet"

    Scenario: Delete a target from an application again
        Given there is an application with name="myapp"
        And there is a package with version="123"
        When I run "package delete myapp 123"
        Then the output is "This command is not implemented yet"
