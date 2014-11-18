@no_db
Feature: Authorization roles
    As a user
    I want authorization limitations
    So that I can't break things I'm not supposed to

    Scenario Outline:
        Given there is an environment with name="dev"
        And I am in the "dev" environment
        And I have "dev" permissions
        When I run "<command>"
        Then the output is "You do not have the appropriate permissions to run this command. Contact your manager."

        Examples:
            | command                                      |
            | application add myapp myjob                  |
            | application delete myapp                     |
            | application add-apptype myapp proj targ      |
            | application delete-apptype myapp proj targ   |
            | project add proj                             |
            | project delete proj                          |
