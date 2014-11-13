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
            | project               | -h        |
            | project add           | -h        |
            | project delete        | -h        |
            | project list          | -h        |
            | package               | -h        |
            | package add           | -h        |
            | package delete        | -h        |
            | package list          | -h        |
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
            | project               | --help    |
            | project add           | --help    |
            | project delete        | --help    |
            | project list          | --help    |
            | package               | --help    |
            | package add           | --help    |
            | package delete        | --help    |
            | package list          | --help    |
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
