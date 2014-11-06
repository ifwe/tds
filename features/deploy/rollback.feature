Feature: (config revert|deploy rollback) project [--delay] [--hosts|--apptypes|--all-apptypes]
    As a developer
    I want to redeploy older versions of projects to targets
    So that I can correct problems with services easily

    Background:
        Given I have "stage" permissions
        And I am in the "stage" environment
        And there is a project with name="proj"
        And there is a deploy target with name="the-apptype"
        And the deploy target is a part of the project-application pair
        And there are hosts:
            | name          | env   |
            | projhost01    | stage |
            | projhost02    | stage |
        And the hosts are associated with the deploy target

        And there is a package with version="121"
        And the package is deployed on the deploy target
        And the package has been validated

        And there is a package with version="122"
        And the package is deployed on the deploy target
        And the package has been invalidated

        And there is a package with version="123"
        And the package is deployed on the deploy target
        And the package has been validated

    Scenario Outline: rollback project that doesn't exist
        When I run "<command> doesnt-exist"
        Then the output has "Project "doesnt-exist" does not exist"

        Examples:
            | command           |
            | config revert     |
            | deploy rollback   |

    Scenario Outline: rollback version to host that doesn't exist
        When I run "<command> proj --hosts badhost01"
        Then the output has "These hosts do not exist: badhost01"
        Examples:
            | command           |
            | config revert     |
            | deploy rollback   |

    Scenario Outline: rollback version to apptype that doesn't exist
        When I run "<command> proj --apptype bad-apptype"
        Then the output has "Valid apptypes for project "proj" are: ['the-apptype']"

        Examples:
            | command           |
            | config revert     |
            | deploy rollback   |

    Scenario Outline: rollback command with no specifier
        When I run "<command> proj"
        Then the output has "Completed: 2 out of 2 hosts"
        And package "proj-name" version "121" was deployed to the deploy target

        Examples:
            | command           |
            | config revert     |
            | deploy rollback   |

    Scenario Outline: rollback version to hosts
        Given there is a package with version="124"
        And the package is deployed on the hosts
        When I run "<command> proj --hosts projhost01 projhost02"
        Then the output has "Completed: 2 out of 2 hosts"
        And package "proj-name" version "123" was deployed to the hosts

        Examples:
            | command           |
            | config revert     |
            | deploy rollback   |

    Scenario Outline: rollback version to apptype
        When I run "<command> proj --apptype the-apptype"
        Then the output has "Completed: 2 out of 2 hosts"
        And package "proj-name" version "121" was deployed to the deploy target

        Examples:
            | command           |
            | config revert     |
            | deploy rollback   |

    Scenario Outline: rollback version to all apptypes
        Given there is a deploy target with name="another-apptype"
        And the deploy target is a part of the project-application pair
        And there is a host with name="anotherhost01"
        And the host is associated with the deploy target

        And the package "121" is deployed on the deploy target
        And the package "121" is validated

        And the package "122" is deployed on the deploy target
        And the package "122" is invalidated

        And the package "123" is deployed on the deploy target
        And the package "123" is validated

        When I run "<command> proj --all-apptypes"
        Then the output has "Completed: 2 out of 2 hosts"
        And the output has "Completed: 1 out of 1 hosts"
        And package "proj-name" version "121" was deployed to the deploy targets

        Examples:
            | command           |
            | config revert     |
            | deploy rollback   |

    Scenario Outline: rollback version to hosts with a failure
        Given the host "projhost01" will fail to deploy
        When I run "<command> proj --hosts projhost01 projhost02"
        Then the output has "Some hosts had failures"
        And the output has "Hostname: projhost01"

        Examples:
            | command           |
            | config revert     |
            | deploy rollback   |

    Scenario Outline: rollback version to apptype with a failure
        Given the host "projhost01" will fail to deploy
        When I run "<command> proj --apptype the-apptype"
        Then the output has "Some hosts had failures"
        And the output has "Hostname: projhost01"

        Examples:
            | command           |
            | config revert     |
            | deploy rollback   |

    Scenario Outline: rollback version to all apptypes with a failure
        Given there is a deploy target with name="another-apptype"
        And the deploy target is a part of the project-application pair
        And there is a host with name="anotherhost01"
        And the host is associated with the deploy target

        And the package "121" is deployed on the deploy target
        And the package has been validated

        And the package "122" is deployed on the deploy target
        And the package has been invalidated

        And the package "123" is deployed on the deploy target
        And the package has been validated

        And the host "projhost01" will fail to deploy
        When I run "<command> proj --all-apptypes"
        Then the output has "Some hosts had failures"
        And the output has "Hostname: projhost01"

        Examples:
            | command           |
            | config revert     |
            | deploy rollback   |

    @delay
    Scenario Outline: rollback version with delay option
        When I run "<command> proj --delay 10"
        Then the output has "Completed: 2 out of 2 hosts"
        And package "proj-name" version "121" was deployed to the deploy target
        And it took at least 10 seconds

        Examples:
            | command           |
            | config revert     |
            | deploy rollback   |
