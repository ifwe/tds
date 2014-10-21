Feature: Debug switches
    As a user
    I want debug information
    So that I can find out what's going on deeper in the program

    Scenario Outline: debug package list
        Given I have "dev" permissions
        And I am in the "dev" environment
        And there are projects:
            | name |
            | bar  |
            | foo  |
        And there are packages:
            | version   |
            | 1         |
            | 2         |
            | 3         |
        When I run "<switch> <command>"
        Then the output has "DEBUG"

    Examples:
        | switch | command       |
        | -v     | package list  |
        | -vv    | package list  |
        | -vvv   | package list  |

    Scenario Outline: debug deploy promote
        Given I have "stage" permissions
        And I am in the "stage" environment
        And there is a project with name="proj"
        And there is a deploy target with name="the-apptype"
        And there is a package with version="123"
        And the package version is deployed on the deploy targets in the "dev" env
        And the package version has been validated in the "development" environment
        And there are hosts:
            | name          | env   |
            | dprojhost01   | dev   |
            | dprojhost02   | dev   |
            | sprojhost01   | stage |
            | sprojhost02   | stage |
        And the deploy target is a part of the project
        And the hosts are associated with the deploy target
        When I run "<switch> <command> proj 123 <targets>"
        Then the output has "DEBUG"

        Examples:
            | switch | command          | targets                           |
            | -v     | deploy promote   | --hosts sprojhost01 sprojhost02   |
            | -vv    | deploy promote   | --hosts sprojhost01 sprojhost02   |
            | -vvv   | deploy promote   | --hosts sprojhost01 sprojhost02   |
            | -v     | deploy promote   | --all-apptypes                    |
            | -vv    | deploy promote   | --all-apptypes                    |
            | -vvv   | deploy promote   | --all-apptypes                    |
            | -v     | deploy promote   | --apptypes the-apptype            |
            | -vv    | deploy promote   | --apptypes the-apptype            |
            | -vvv   | deploy promote   | --apptypes the-apptype            |

    Scenario Outline: debug deploy validate
        Given I have "dev" permissions
        And I am in the "dev" environment
        And there is a project with name="proj"
        And there is a deploy target with name="foo"
        And there is a package with version="123"
        And there are hosts:
            | name          |
            | projhost01    |
            | projhost02    |
        And the deploy target is a part of the project
        And the hosts are associated with the deploy target
        And the package version is deployed on the deploy target
        When I run "<switch> <command> proj 123 --apptype foo"
        Then the output has "DEBUG"

        Examples:
            | switch | command          |
            | -v     | deploy validate  |
            | -vv    | deploy validate  |
            | -vvv   | deploy validate  |

    Scenario Outline: debug deploy invalidate
        Given I have "dev" permissions
        And I am in the "dev" environment
        Given there is a project with name="proj"
        And there is a package with version="123"
        And there is a deploy target with name="foo"
        And the deploy target is a part of the project
        And the package version is deployed on the deploy targets
        And the package version has been validated
        When I run "<switch> <command> proj 123 --apptype foo"
        Then the output has "DEBUG"

        Examples:
            | switch | command           |
            | -v     | deploy invalidate |
            | -vv    | deploy invalidate |
            | -vvv   | deploy invalidate |
