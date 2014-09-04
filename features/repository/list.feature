Feature: The repository list subcommand
    As a developer
    I want to view all projects and certain projects
    To determine the state of the projects

    Background: User setup
        Given I have "dev" permissions
        And I am in the "dev" environment

    Scenario: with no projects
        When I run "repository list"
        Then the output is empty

    Scenario: with multiple projects
        Given there are projects:
            | name  |
            | foo   |
            | bar   |
            | baz   |

        When I run "repository list"
        Then the output describes the projects

    Scenario: with missing project specified
        When I run "repository list --projects foo"
        Then the output describes a missing project with name="foo"

    Scenario Outline: with existing project specified
        Given there is a project with name="<name>"
        When I run "repository list --projects <name>"
        Then the output describes a project with name="<name>"

        Examples:
            | name    |
            | foo     |
            | spammon |

    Scenario: with multiple existing projects specified
        Given there are projects:
            | name  |
            | foo   |
            | bar   |

        When I run "repository list --projects foo bar"
        Then the output describes the projects

    Scenario: with a missing project and an existing project specified
        Given there is a project with name="foo"
        When I run "repository list --projects foo bar"
        Then the output describes a missing project with name="bar"

    Scenario: with multiple missing projects specifed
        When I run "repository list --projects foo bar"
        Then the output describes a missing project with name="foo"
        And the output describes a missing project with name="foo"

    Scenario Outline: with explicit blocks output format
        Given there is a project with name="<name>"
        When I run "--output-format blocks repository list --projects <name>"
        Then the output describes a project with name="<name>"

        Examples:
            | name    |
            | foo     |
            | spammon |

    Scenario Outline: with table output format
        Given there is a project with name="<name>"
        When I run "--output-format table repository list --projects <name>"
        Then the output describes a project with name="<name>" in a table

        Examples:
            | name    |
            | foo     |
            | spammon |

    Scenario: invalid output format
        When I run "--output-format foo repository list"
        Then the output has "output-format must be one of"

    Scenario Outline: with json output format
        Given there is a project with name="<name>"
        When I run "--output-format json repository list --projects <name>"
        Then the output describes a project with name="<name>" in json

        Examples:
            | name    |
            | foo     |
            | spammon |
