Feature: The package list subcommand
    As a developer
    I want to view all packages and packages for certain projects
    To determine the state of the packages

    Background: User setup
        Given I have "dev" permissions
        And I am in the "dev" environment
        And there are applications:
            | name |
            | bar  |
            | foo  |

    Scenario Outline: missing packages
        When I run "package list <args>"
        Then the output is empty

        Examples:
            | args                      |
            |                           |
            | --application foo         |
            | --applications foo bar    |

    Scenario: with multiple packages
        Given there are packages:
            | version   |
            | 1         |
            | 2         |
            | 3         |
        When I run "package list"
        Then the output describes the packages

    Scenario: with existing application specified
        Given there is a package with version="1"
        When I run "package list --applications bar"
        Then the output describes the packages

    Scenario: with multiple existing application specified
        Given there are packages:
            | name  | version |
            | foo   | 1       |
            | foo   | 2       |
        When I run "package list --applications foo bar"
        Then the output describes the packages

    Scenario: with a missing project and an existing project specified
        Given there is a package with project="foo",version="5"
        When I run "package list --projects foo bar"
        Then the output describes a package version with name="foo-name",version="5"

    Scenario: with table output format
        Given there is a package version with version="1"
        When I run "--output-format table package list --projects bar"
        Then the output describes the packages in a table

    Scenario: explicit blocks output format
        Given there is a package version with version="1"
        When I run "--output-format blocks package list --projects bar"
        Then the output describes the packages

    Scenario: invalid output format
        When I run "--output-format foo package list"
        Then the output has "usage:"

    Scenario: with json output format
        Given there is a package version with version="1"
        When I run "--output-format json package list --projects bar"
        Then the output describes the packages in json

    Scenario: with latex output format
        Given there is a package version with version="1"
        When I run "--output-format latex package list --projects bar"
        Then the output describes the packages in latex

    Scenario: with rst output format
        Given there is a package version with version="1"
        When I run "--output-format rst package list --project bar"
        Then the output describes the packages in rst

    Scenario: with a missing application and an existing application specified
        Given there is a package with name="foo",version="5"
        When I run "package list --applications foo bar"
        Then the output describes a package with name="foo",version="5"
