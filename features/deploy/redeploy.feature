Feature: (config repush|deploy redeploy) project [--delay] [--hosts|--apptypes|--all-apptypes]
    As a developer
    I want to redeploy failed deployments to targets
    So I can complete a given deployment fully

    Background:
        Given I have "stage" permissions
        And I am in the "stage" environment
        And there is a project with name="proj"
        And there is a deploy target with name="the-apptype"
        And the deploy target is a part of the project
        And there are hosts:
            | name          | env     |
            | dprojhost01   | dev     |
            | dprojhost02   | dev     |
            | sprojhost01   | stage   |
            | sprojhost02   | stage   |
        And the hosts are associated with the deploy target

        And there is a package with version="122"
        And the package is deployed on the deploy targets in the "stage" env
        And the package has been validated in the "staging" environment

        And there is a package with version="123"
        And the package is deployed on the deploy targets in the "dev" env
        And the package has been validated in the "development" environment
        And the package is deployed on the deploy targets in the "stage" env
        And the package failed to deploy on the host with name="sprojhost02"

    Scenario Outline: redeploy project that doesn't exist
        When I run "<command> doesnt-exist"
        Then the output has "Project "doesnt-exist" does not exist"

        Examples:
            | command           |
            | config repush     |
            | deploy redeploy   |

    Scenario Outline: redeploy to host that doesn't exist
        When I run "<command> proj --hosts badhost01"
        Then the output has "These hosts do not exist: badhost01"

        Examples:
            | command           |
            | config repush     |
            | deploy redeploy   |

    Scenario Outline: redeploy to apptype that doesn't exist
        When I run "<command> proj --apptype bad-apptype"
        Then the output has "Valid apptypes for project "proj" are: ['the-apptype']"

        Examples:
            | command           |
            | config repush     |
            | deploy redeploy   |

    Scenario Outline: redeploy to hosts
        When I run "<command> proj --hosts sprojhost02"
        Then the output has "Completed: 1 out of 1 hosts"
        And package "proj-name" version "123" was deployed to host "sprojhost02"

        Examples:
            | command           |
            | config repush     |
            | deploy redeploy   |

    Scenario Outline: redeploy to apptype
        When I run "<command> proj --apptype the-apptype"
        Then the output has "Completed: 2 out of 2 hosts"
        And the output has "Host "sprojhost01" already has "proj-name@123" successfully deployed, skipping"
        And package "proj-name" version "123" was deployed to host "sprojhost02"

        Examples:
            | command           |
            | config repush     |
            | deploy redeploy   |

    Scenario Outline: redeploy to all apptypes
        Given there is a deploy target with name="another-apptype"
        And there is a host with name="anotherhost01"
        And the host is associated with the deploy target
        And the deploy target is a part of the project
        And the package is deployed on the deploy target
        And the package failed to deploy on the host with name="anotherhost01"
        When I run "<command> proj --all-apptypes"
        Then the output has "Completed: 2 out of 2 hosts"
        And the output has "Completed: 1 out of 1 hosts"
        And package "proj-name" version "123" was deployed to host "sprojhost02"
        And package "proj-name" version "123" was deployed to host "anotherhost01"

        Examples:
            | command           |
            | config repush     |
            | deploy redeploy   |

    Scenario Outline: redeploy to host with a failure
        Given the host "sprojhost02" will fail to deploy
        When I run "<command> proj --hosts sprojhost02"
        Then the output has "Some hosts had failures"
        And the output has "Hostname: sprojhost02"

        Examples:
            | command           |
            | config repush     |
            | deploy redeploy   |

    Scenario Outline: redeploy to apptype with a failure
        Given the host "sprojhost02" will fail to deploy
        When I run "<command> proj --apptype the-apptype"
        Then the output has "Some hosts had failures"
        And the output has "Hostname: sprojhost02"

        Examples:
            | command           |
            | config repush     |
            | deploy redeploy   |

    Scenario Outline: redeploy to all apptypes with a failure
        Given the host "sprojhost02" will fail to deploy
        When I run "<command> proj --all-apptypes"
        Then the output has "Some hosts had failures"
        And the output has "Hostname: sprojhost02"

        Examples:
            | command           |
            | config repush     |
            | deploy redeploy   |

    @delay
    Scenario Outline: redeploy with delay option
        When I run "<command> proj --delay 10"
        Then the output has "Completed: 2 out of 2 hosts"
        And package "proj-name" version "123" was deployed to host "sprojhost02"
        And the output has "Host "sprojhost01" already has "proj-name@123" successfully deployed, skipping"
        And it took at least 10 seconds

        Examples:
            | command           |
            | config repush     |
            | deploy redeploy   |
