Feature: project delete project
    As an administrator
    I want to delete a project
    To clean up things that don't exist anymore

    @no_db
    Scenario: too few arguments
        When I run "project delete"
        Then the output has "usage:"

    @no_db
    Scenario: invalid arguments
        When I run "project delete --foo"
        Then the output has "usage:"

    Scenario: for admin with existing project
        Given I have "admin" permissions
        And there is a project with name="proj"
        When I run "project delete proj"
        Then the output has "Project "proj" was successfully deleted"
        And there is no project with name="proj"

    Scenario: for admin with non-existing project
        Given I have "admin" permissions
        When I run "project delete proj"
        Then the output has "Project does not exist: proj"
        And there is no project with name="proj"
