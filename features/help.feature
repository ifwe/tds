@no_db
Feature: Help switches
    As a user
    I want help text
    So that I can learn how to use the program

    Scenario Outline: help
        When I run "<command> <switch>"
        Then the output has "usage:"

        Examples:
            | command               | switch    |
            |                       | -h        |
            | repository            | -h        |
            | repository list       | -h        |
            | repository add        | -h        |
            | repository delete     | -h        |
            | package               | -h        |
            | package add           | -h        |
            | package delete        | -h        |
            | package list          | -h        |
            | config                | -h        |
            | config add-apptype    | -h        |
            | config create         | -h        |
            | config delete-apptype | -h        |
            | config invalidate     | -h        |
            | config push           | -h        |
            | config repush         | -h        |
            | config revert         | -h        |
            | config show           | -h        |
            | config validate       | -h        |
            | deploy                | -h        |
            | deploy add-apptype    | -h        |
            | deploy delete-apptype | -h        |
            | deploy invalidate     | -h        |
            | deploy promote        | -h        |
            | deploy redeploy       | -h        |
            | deploy restart        | -h        |
            | deploy rollback       | -h        |
            | deploy show           | -h        |
            | deploy validate       | -h        |
            |                       | --help    |
            | repository            | --help    |
            | repository list       | --help    |
            | repository add        | --help    |
            | repository delete     | --help    |
            | package               | --help    |
            | package add           | --help    |
            | package delete        | --help    |
            | package list          | --help    |
            | config                | --help    |
            | config add-apptype    | --help    |
            | config create         | --help    |
            | config delete-apptype | --help    |
            | config invalidate     | --help    |
            | config push           | --help    |
            | config repush         | --help    |
            | config revert         | --help    |
            | config show           | --help    |
            | config validate       | --help    |
            | deploy                | --help    |
            | deploy add-apptype    | --help    |
            | deploy delete-apptype | --help    |
            | deploy invalidate     | --help    |
            | deploy promote        | --help    |
            | deploy redeploy       | --help    |
            | deploy restart        | --help    |
            | deploy rollback       | --help    |
            | deploy show           | --help    |
            | deploy validate       | --help    |
