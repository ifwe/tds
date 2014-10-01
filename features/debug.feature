Feature: Debug switches
    As a user
    I want debug information
    So that I can find out what's going on deeper in the program

    Background: User setup
        Given I have "dev" permissions
        And I am in the "dev" environment
        And there are projects:
            | name |
            | bar  |
            | foo  |
        And there are package versions:
            | version   |
            | 1         |
            | 2         |
            | 3         |

    Scenario Outline: debug
        When I run "<switch> <command>"
        Then the output has "DEBUG"

    Examples:
        | switch | command       |
        | -v     | package list  |
        | -vv    | package list  |
        | -vvv   | package list  |
