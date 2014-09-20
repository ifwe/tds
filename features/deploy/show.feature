Feature: deploy/config show subcommand
    As a user
    I want to show deployed targets to projects
    So I can determine the state of the deployments to the projects

    Background:
        Given I have "dev" permissions
        And I am in the "dev" environment
        And there is a project with name="proj"
        And there is a deploy target with name="foo"
        And the deploy target is a part of the project
        And there are hosts:
            | name          | env   |
            | projhost01    | dev   |
            | projhost02    | dev   |
        And the hosts are associated with the deploy target
        And there is a package version with version="123"

    Scenario Outline: too few arguments
        When I run "<command> show"
        Then the output has "usage:"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: too many arguments
        When I run "<command> show proj 123 foo"
        Then the output has "usage:"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: with a project that doesn't exist
        When I run "<command> show badproj"
        Then the output is "Project "badproj" does not exist"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: with a project and a version that doesn't exist
        When I run "<command> show proj 123"
        Then the output describes no deployments

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: with a project and an apptype that doesn't exist
        When I run "<command> show proj --apptypes bar"
        Then the output is "Valid apptypes for project "proj" are: ['foo']"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: with a project and an apptype and a version that doesn't exist
        When I run "<command> show proj 124 --apptypes foo"
        Then the output describes no deployments

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: with a project and a version for a tier
        Given the package version is deployed on the deploy target
        And the package version is validated
        When I run "<command> show proj 123"
        Then the output describes the app deployments

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: with a project and an apptype
        Given the package version is deployed on the deploy target
        And the package version is validated
        When I run "<command> show proj --apptypes foo"
        Then the output describes the app deployments

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: with a project and a version and an apptype
        Given the package version is deployed on the deploy target
        And the package version is validated
        When I run "<command> show proj 123 --apptypes foo"
        Then the output describes the app deployments

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: without package version validation
        Given the package version is deployed on the deploy target
        When I run "<command> show proj 123 --apptypes foo"
        Then the output describes the app deployments
        And the output describes the host deployments

    Examples:
        | command |
        | deploy  |
        | config  |

# TODO: need to write tests for host-only deployments
