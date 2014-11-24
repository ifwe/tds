Feature: project list [proj [proj [...]]]
    As a developer
    I want to view all projects and certain projects
    To determine the state of the projects

    Background: User setup
        Given I have "dev" permissions
        And there is an environment with name="dev"
        And I am in the "dev" environment

    Scenario: with no projects
        When I run "project list"
        Then the output is empty

    Scenario: with multiple projects
        Given there are projects:
            | name  |
            | foo   |
            | bar   |
            | baz   |

        When I run "project list"
        Then the output describes the projects

    Scenario: with missing project specified
        When I run "project list foo"
        Then the output describes a missing project with name="foo"

    Scenario Outline: with existing project specified
        Given there is a project with name="<name>"
        When I run "project list <name>"
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

        When I run "project list foo bar"
        Then the output describes the projects

    Scenario: with a missing project and an existing project specified
        Given there is a project with name="foo"
        When I run "project list foo bar"
        Then the output describes a missing project with name="bar"

    Scenario: with multiple missing projects specifed
        When I run "project list foo bar"
        Then the output describes a missing project with name="foo",name="bar"

    Scenario Outline: with explicit blocks output format
        Given there is a project with name="<name>"
        When I run "--output-format blocks project list <name>"
        Then the output describes a project with name="<name>"

        Examples:
            | name    |
            | foo     |
            | spammon |

    Scenario Outline: with table output format
        Given there is a project with name="<name>"
        When I run "--output-format table project list <name>"
        Then the output describes a project with name="<name>" in a table

        Examples:
            | name    |
            | foo     |
            | spammon |

    Scenario: invalid output format
        When I run "--output-format foo project list"
        Then the output has "usage:"

    Scenario Outline: with json output format
        Given there is a project with name="<name>"
        When I run "--output-format json project list <name>"
        Then the output describes a project with name="<name>" in json

        Examples:
            | name    |
            | foo     |
            | spammon |

    Scenario Outline: with latex output format
        Given there is a project with name="<name>"
        When I run "--output-format latex project list <name>"
        Then the output describes a project with name="<name>" in latex

        Examples:
            | name    |
            | foo     |
            | spammon |

    Scenario Outline: with rst output format
        Given there is a project with name="<name>"
        When I run "--output-format rst project list <name>"
        Then the output describes a project with name="<name>" in rst

        Examples:
            | name    |
            | foo     |
            | spammon |
