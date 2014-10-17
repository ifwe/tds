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
        Then the output is "Package "proj-name@124" does not exist"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: with --apptypes and --all-apptypes
        When I run "<command> show proj 123 --all-apptypes --apptypes foo"
        Then the output is "Only one of the "--hosts", "--apptypes" or "--all-apptypes" options may be used at a given time"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: with a project and a version for a tier
        Given the package version is deployed on the deploy target
        And the package version has been validated
        When I run "<command> show proj 123"
        Then the output describes the app deployments

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: with a project and an apptype
        Given the package version is deployed on the deploy target
        And the package version has been validated
        When I run "<command> show proj --apptypes foo"
        Then the output describes the app deployments

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: with a project and a version and an apptype
        Given the package version is deployed on the deploy target
        And the package version has been validated
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

    Scenario Outline: host-only deployments with all-apptypes
        Given the package version is deployed on the hosts
        When I run "<command> show proj 123 --all-apptypes"
        Then the output describes the host deployments

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: host-only deployments with specific apptype
        Given the package version is deployed on the hosts
        When I run "<command> show proj 123 --apptypes foo"
        Then the output describes the host deployments

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: with a different version deployed to hosts
        Given the package version is deployed on the deploy target
        And there is a package version with version="200"
        And the package version is deployed on the hosts
        When I run "<command> show proj --apptypes foo"
        Then the output describes the host deployments
        And the output describes an app deployment with version="123"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: check host output for different deployment to hosts
        Given the package version is deployed on the deploy target
        And there is a package version with version="200"
        And the package version is deployed on the hosts
        When I run "<command> show proj 200 --apptypes foo"
        Then the output describes the host deployments
        And the output does not describe an app deployment with name="proj-name"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: check app output for different deployment to hosts
        Given the package version is deployed on the deploy target
        And there is a package version with version="200"
        And the package version is deployed on the hosts
        When I run "<command> show proj 123 --apptypes foo"
        Then the output describes an app deployment with version="123"
        And the output does not describe a host deployment with pkg_name="proj-name"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: different version deployed to only one host
        Given the package version is deployed on the deploy target
        And there is a package version with version="200"
        And the package version is deployed on the host with name="projhost01"
        When I run "<command> show proj 200 --apptypes foo"
        Then the output describes a host deployment with pkg_name="proj-name",host_name="projhost01"
        And the output does not describe a host deployment with host_name="projhost02"
        And the output does not describe an app deployment with name="proj-name"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: check app output with different version deployed to only one host
        Given the package version is deployed on the deploy target
        And there is a package version with version="200"
        And the package version is deployed on the host with name="projhost01"
        When I run "<command> show proj 123 --apptypes foo"
        Then the output describes a host deployment with pkg_name="proj-name",host_name="projhost02"
        And the output describes an app deployment with name="proj-name"
        And the output does not describe a host deployment with host_name="projhost01"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: different versions with validation
        Given the package version is deployed on the deploy target
        And the package version has been validated
        And there is a package version with version="200"
        And the package version is deployed on the host with name="projhost01"
        When I run "<command> show proj 123 --apptypes foo"
        Then the output describes an app deployment with name="proj-name",version="123"
        And the output does not describe a host deployment with pkg_name="proj-name"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: host output with different version with validation
        Given the package version is deployed on the deploy target
        And the package version has been validated
        And there is a package version with version="200"
        And the package version is deployed on the host with name="projhost01"
        When I run "<command> show proj 200 --apptypes foo"
        Then the output describes a host deployment with pkg_name="proj-name",host_name="projhost01"
        And the output does not describe a host deployment with host_name="projhost02"
        And the output does not describe an app deployment with name="proj-name"

        Examples:
            | command |
            | deploy  |
            | config  |
