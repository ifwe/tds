Feature: project add project
    As an administrator
    I want to add projects to the repository
    So that developers can deploy the projects with TDS

    Background:
        Given I have "admin" permissions

    @no_db
    Scenario: too few arguments
        When I run "project add"
        Then the output has "usage:"

    @no_db
    Scenario: too many arguments
        When I run "project add proj foo"
        Then the output has "usage:"

    Scenario: add new project
        When I run "project add proj"
        Then there is a project with name="proj"
        And the output has "Created proj:"
        And the output describes a project with name="proj"

    @wip
    Scenario: add project that already exists
        Given there is a project with name="proj"
        When I run "project add proj"
        Then the output is "Project already exists: proj"
