Feature: The package list subcommand
    As a developer
    I want to view all packages and packages for certain projects
    To determine the state of the packages

    Background: User setup
        Given I have "dev" permissions
        And I am in the "dev" environment
        And there are projects:
            | name |
            | bar  |
            | foo  |

    Scenario Outline: missing packages
        When I run "package list <args>"
        Then the output is empty

        Examples:
            | args                  |
            |                       |
            | --projects foo        |
            | --projects foo bar    |

    Scenario: with multiple packages
        Given there are package versions:
            | version   |
            | 1         |
            | 2         |
            | 3         |
        When I run "package list"
        Then the output describes the packages

    Scenario: with existing project specified
        Given there is a package version with version="1"
        When I run "package list --projects bar"
        Then the output describes the packages

    Scenario: with multiple existing projects specified
        Given there are package versions:
            | project   | version |
            | foo       | 1       |
            | foo       | 2       |
        When I run "package list --projects foo bar"
        Then the output describes the packages

    Scenario: with a missing project and an existing project specified
        Given there is a package version with project="foo",version="5"
        When I run "package list --projects foo bar"
        Then the output describes a package version with name="foo-name",version="5"