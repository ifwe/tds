Feature: application list [app [app [...]]]
    As a developer
    I want to view all applications and certain applications
    To know what software is availble to me via TDS

    Background: User setup
        Given I have "dev" permissions
        And there is an environment with name="dev"
        And I am in the "dev" environment
        And there is an application with name="app1"
        And there is an application with name="app2",arch="x86_64",path="app2"
        And there is an application with name="app3",build_type="developer",path="myapp"

    Scenario: with invalid argument
        When I run "application list --foo"
        Then the output has "usage:"

    Scenario: with no arguments
        When I run "application list"
        Then the output describes the applications

    Scenario: with existing application specified
        When I run "application list app2"
        Then the output describes an application with name="app2"

    Scenario: with multiple existing applications specified
        When I run "application list app1 app3"
        Then the output describes an application with name="app1"
        And the output describes an application with name="app3"

    Scenario: with missing application specified
        When I run "application list foo"
        Then the output describes a missing application with name="foo"

    Scenario: with an existing application and a missing application specified
        When I run "application list app1 foo"
        Then the output describes a missing application with name="foo"

    Scenario: with multiple missing applications specified
        When I run "application list foo bar"
        Then the output describes a missing application with name="foo",name="bar"

    Scenario: invalid output format
        When I run "--output-format foo application list"
        Then the output has "usage:"

    Scenario Outline: with various output format
        When I run "--output-format <format> application list app1"
        Then the output describes an application in <format> with name="app1"

        Examples:
            | format  |
            | table   |
            | json    |
            | rst     |
            | latex   |
