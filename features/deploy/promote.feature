Feature: (config push|deploy promote) project version [-f|--force] [--delay] [--hosts|--apptypes|--all-apptypes] (-f/--force only for deploy promote)
    As a developer
    I want to deploy projects to targets
    So that I can update services easily

    Background:
        Given I have "stage" permissions
        And I am in the "stage" environment
        And there is a project with name="proj"
        And there is a deploy target with name="the-apptype"
        And there is a package version with version="123"
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

    Scenario Outline: promote project that doesn't exist
        When I run "<command> doesnt-exist 456"
        Then the output is "Project "doesnt-exist" does not exist"

        Examples:
            | command           |
            | config push       |
            | deploy promote    |

    Scenario Outline: promote version that doesn't exist
        When I run "<command> proj 456"
        Then the output is "Package "proj@456" does not exist"

        Examples:
            | command           |
            | config push       |
            | deploy promote    |

    Scenario Outline: promote version to host that doesn't exist
        When I run "<command> proj 123 --hosts badhost01"
        Then the output has "These hosts do not exist: badhost01"
        Examples:
            | command           |
            | config push       |
            | deploy promote    |

    Scenario Outline: promote version to apptype that doesn't exist
        When I run "<command> proj 123 --apptype bad-apptype"
        Then the output has "Valid apptypes for project "proj" are: ['the-apptype']"

        Examples:
            | command           |
            | config push       |
            | deploy promote    |

    Scenario: promote version that isn't validated in previous env (only for deploy)
        Given there is a package version with version="124"
        When I run "deploy promote proj 124"
        Then the output has "Package "proj@124" never validated in "dev" environment for target "the-apptype""

    Scenario Outline: promote version to hosts
        When I run "<command> proj 123 --hosts sprojhost01 sprojhost02"
        Then the output has "Completed: 2 out of 2 hosts"
        And package "proj-name" version "123" was deployed to the hosts

        Examples:
            | command           |
            | config push       |
            | deploy promote    |

    Scenario Outline: promote version to apptype
        When I run "<command> proj 123 --apptype the-apptype"
        Then the output has "Completed: 2 out of 2 hosts"
        And package "proj-name" version "123" was deployed to the deploy target

        Examples:
            | command           |
            | config push       |
            | deploy promote    |

    Scenario Outline: promote version to all apptypes
        Given there is a deploy target with name="another-apptype"
        And there is a host with name="anotherhost01"
        And the host is associated with the deploy target
        And the deploy target is a part of the project
        And the package version is deployed on the deploy targets in the "dev" env
        And the package version has been validated in the "development" environment
        When I run "<command> proj 123 --all-apptypes"
        Then the output has "Completed: 2 out of 2 hosts"
        And the output has "Completed: 1 out of 1 hosts"
        And package "proj-name" version "123" was deployed to the deploy targets

        Examples:
            | command           |
            | config push       |
            | deploy promote    |

    Scenario Outline: promote version to hosts with a failure
        Given the host "sprojhost01" will fail to deploy
        When I run "<command> proj 123 --hosts sprojhost01 sprojhost02"
        Then the output has "Some hosts had failures"
        And the output has "Hostname: sprojhost01"


        Examples:
            | command           |
            | config push       |
            | deploy promote    |

    Scenario Outline: promote version to apptype with a failure
        Given the host "sprojhost01" will fail to deploy
        When I run "<command> proj 123 --apptype the-apptype"
        Then the output has "Some hosts had failures"
        And the output has "Hostname: sprojhost01"

        Examples:
            | command           |
            | config push       |
            | deploy promote    |

    Scenario Outline: promote version to all apptypes with a failure
        Given the host "sprojhost01" will fail to deploy
        When I run "<command> proj 123 --all-apptypes"
        Then the output has "Some hosts had failures"
        And the output has "Hostname: sprojhost01"

        Examples:
            | command           |
            | config push       |
            | deploy promote    |

    Scenario Outline: promote version to with delay option
        When I run "<command> proj 123 --delay 10"
        Then the output has "Completed: 2 out of 2 hosts"
        And package "proj-name" version "123" was deployed to the deploy target
        And it took at least 10 seconds

        Examples:
            | command           |
            | config push       |
            | deploy promote    |

    Scenario Outline: promote version that isn't validated in previous env with force option
        Given there is a package version with version="124"
        When I run "deploy promote <switch> proj 124"
        Then the output has "Completed: 2 out of 2 hosts"
        And package "proj-name" version "124" was deployed to the deploy target

        Examples:
            | switch    |
            | -f        |
            | --force   |
