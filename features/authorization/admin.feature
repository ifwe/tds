@no_db
Feature: Authorization roles
    As a user
    I want authorization limitations
    So that I can't break things I'm not supposed to

    Scenario Outline:
        Given I am in the "dev" environment
        And I have "dev" permissions
        When I run "<command>"
        Then the output is "You do not have the appropriate permissions to run this command. Contact your manager."

        Examples:
            | command                                       |
            | deploy delete-apptype foo bar                 |
            | deploy add-apptype foo bar baz                |
            | config create foo bar baz noarch ci rpm       |
            | config delete foo                             |
            # | project delete                                |
            # | project create                                |
            | repository delete foo                         |
            | repository add foo bar baz noarch ci rpm what |
