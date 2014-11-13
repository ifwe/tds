@no_db
Feature: Authorization roles - environment
    As a user
    I want authorization limitations
    So that I can't break things I'm not supposed to

    Scenario Outline:
        Given I am in the "dev" environment
        And I have "no" permissions
        When I run "<command>"
        Then the output is "You do not have the appropriate permissions to run this command. Contact your manager."

        Examples:
            | command                   |
            | application list          |
            | deploy invalidate foo 123 |
            | deploy show foo           |
            | deploy validate foo 123   |
            | deploy promote foo 123    |
            | deploy redeploy foo       |
            | deploy rollback foo       |
            | deploy restart foo        |
            | package list              |
            | package add foo bar 123   |
            | package delete foo 123    |
            | project list              |
