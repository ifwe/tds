Feature: deploy rollback application [--delay] [--hosts|--apptypes|--all-apptypes]
    As a developer
    I want to redeploy older versions of applications to targets
    So that I can correct problems with services easily

    Background:
        Given I have "stage" permissions
        And there are environments
            | name   |
            | dev    |
            | stage  |
        And I am in the "stage" environment
        And there is a project with name="proj"
        And there is an application with name="myapp"
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

        And I wait 1 seconds
        And there is a package with version="122"
        And the package is deployed on the deploy target
        And the package has been invalidated

        And I wait 1 seconds
        And there is a package with version="123"
        And the package is deployed on the deploy target
        And the package has been validated

    Scenario: rollback application that doesn't exist
        When I run "deploy rollback badapp"
        Then the output has "Application does not exist: badapp"

    Scenario: rollback version to host that doesn't exist
        When I run "deploy rollback myapp --hosts badhost01"
        Then the output has "Host does not exist: badhost01"

    Scenario: rollback version to apptype that doesn't exist
        When I run "deploy rollback myapp --apptype bad-apptype"
        Then the output has "Valid apptypes for application "myapp" are: ['the-apptype']"

    Scenario Outline: rollback command with no specifier
        Given the deploy strategy is "<strategy>"
        When I run "deploy rollback myapp"
        Then the output has "Completed: 2 out of 2 hosts"
        And package "myapp" version "121" was deployed to the deploy target

        Examples:
            | strategy |
            | mco      |
            | salt     |

    Scenario Outline: rollback version to hosts
        Given the deploy strategy is "<strategy>"
        And there is a package with version="124"
        And the package is deployed on the hosts
        When I run "deploy rollback myapp --hosts projhost01 projhost02"
        Then the output has "Completed: 2 out of 2 hosts"
        And package "myapp" version "123" was deployed to the hosts

        Examples:
            | strategy |
            | mco      |
            | salt     |

    Scenario Outline: rollback version to apptype
        Given the deploy strategy is "<strategy>"
        When I run "deploy rollback myapp --apptype the-apptype"
        Then the output has "Completed: 2 out of 2 hosts"
        And package "myapp" version "121" was deployed to the deploy target

        Examples:
            | strategy |
            | mco      |
            | salt     |

    Scenario Outline: rollback version to all apptypes
        Given the deploy strategy is "<strategy>"
        And there is a deploy target with name="another-apptype"
        And the deploy target is a part of the project-application pair
        And there is a host with name="anotherhost01"
        And the host is associated with the deploy target

        And the package "121" is deployed on the deploy target
        And the package "121" is validated

        And I wait 1 seconds
        And the package "122" is deployed on the deploy target
        And the package "122" is invalidated

        And I wait 1 seconds
        And the package "123" is deployed on the deploy target
        And the package "123" is validated

        When I run "deploy rollback myapp --all-apptypes"
        Then the output has "Completed: 2 out of 2 hosts"
        And the output has "Completed: 1 out of 1 hosts"
        And package "myapp" version "121" was deployed to the deploy targets

        Examples:
            | strategy |
            | mco      |
            | salt     |

    Scenario Outline: rollback version to hosts with a failure
        Given the deploy strategy is "<strategy>"
        And the host "projhost01" will fail to deploy
        When I run "deploy rollback myapp --hosts projhost01 projhost02"
        Then the output has "Some hosts had failures"
        And the output has "Hostname: projhost01"

        Examples:
            | strategy |
            | mco      |
            | salt     |

    Scenario Outline: rollback version to apptype with a failure
        Given the deploy strategy is "<strategy>"
        And the host "projhost01" will fail to deploy
        When I run "deploy rollback myapp --apptype the-apptype"
        Then the output has "Some hosts had failures"
        And the output has "Hostname: projhost01"

        Examples:
            | strategy |
            | mco      |
            | salt     |

    Scenario Outline: rollback version to all apptypes with a failure
        Given the deploy strategy is "<strategy>"
        And there is a deploy target with name="another-apptype"
        And the deploy target is a part of the project-application pair
        And there is a host with name="anotherhost01"
        And the host is associated with the deploy target

        And the package "121" is deployed on the deploy target
        And the package has been validated

        And I wait 1 seconds
        And the package "122" is deployed on the deploy target
        And the package has been invalidated

        And I wait 1 seconds
        And the package "123" is deployed on the deploy target
        And the package has been validated

        And the host "projhost01" will fail to deploy
        When I run "deploy rollback myapp --all-apptypes"
        Then the output has "Some hosts had failures"
        And the output has "Hostname: projhost01"

        Examples:
            | strategy |
            | mco      |
            | salt     |

    Scenario Outline: rollback a single host out of multiple apptypes
        Given the deploy strategy is "<strategy>"
        And there is a deploy target with name="another-apptype"
        And the deploy target is a part of the project-application pair
        And there is a host with name="anotherhost01"
        And the host is associated with the deploy target
        And there is a host with name="anotherhost02"
        And the host is associated with the deploy target

        And the package "121" is deployed on the deploy target
        And the package has been validated

        And I wait 1 seconds
        And the package "122" is deployed on the deploy target
        And the package has been validated

        And I wait 1 seconds
        And the package "123" is deployed on the deploy target
        And the package has been validated

        And there is a package with version="124"
        And the package "124" is deployed on the deploy target
        And the package has been validated

        When I run "deploy rollback myapp --hosts anotherhost01"
        Then the output has "Completed: 1 out of 1 hosts"

        Examples:
            | strategy |
            | mco      |
            | salt     |

    @delay
    Scenario Outline: rollback version with delay option
        Given the deploy strategy is "<strategy>"
        When I run "deploy rollback myapp --delay 10"
        Then the output has "Completed: 2 out of 2 hosts"
        And package "myapp" version "121" was deployed to the deploy target
        And it took at least 10 seconds

        Examples:
            | strategy |
            | mco      |
            | salt     |
