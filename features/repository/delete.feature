Feature: repository delete project
    As an administrator
    I want to delete a project
    To clean up things that don't exist anymore

    @no_db
    Scenario: too few arguments
        When I run "repository delete"
        Then the output has "usage:"

    @no_db
    Scenario: invalid arguments
        When I run "repository delete --foo"
        Then the output has "usage:"

    @wip
    Scenario: for admin with existing project
        Given I have "admin" permissions
        And there is a project with name="proj"
        When I run "repository delete proj"
        Then the output has "Project "proj" was successfully deleted"
        And there is no project with name="proj"

    Scenario: for admin with non-existing project
        Given I have "admin" permissions
        When I run "repository delete proj"
        Then the output has "Project "proj" does not exist"
        And there is no project with name="proj"
