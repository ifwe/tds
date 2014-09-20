Feature: deploy/config validate subcommand
    As a user
    I want to validate a package on deploy targets
    So I can allow the package to be deployed to the next environment and be redeployed

    Background:
        Given I have "dev" permissions
        And I am in the "dev" environment

    @no_db
    Scenario Outline: too few arguments
        When I run "<command> validate proj"
        Then the output has "usage:"

        Examples:
            | command |
            | deploy  |
            | config  |

    @no_db
    Scenario Outline: too many arguments
        When I run "<command> validate proj vers foo"
        Then the output has "usage:"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: validate a package from a project that doesn't exist
        When I run "<command> validate proj 123"
        Then the output is "Project "proj" does not exist"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: validate a package from a project with a version that doesn't exist
        Given there is a project with name="proj"
        When I run "<command> validate proj 123"
        Then the output is "Package "proj@123" does not exist"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: validate a package from a project for an apptype that doesn't exist
        Given there is a project with name="proj"
        And there is a package version with version="123"
        When I run "<command> validate proj 123 --apptype foo"
        Then the output is "Valid deploy targets for project "proj" are: []"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: validate a package from a project with one of several apptypes that doesn't exist
        Given there is a project with name="proj"
        And there is a package version with version="123"
        And there is a deploy target with name="foo"
        And the deploy target is a part of the project
        When I run "<command> validate proj 123 --apptype foo bar"
        Then the output is "Valid deploy targets for project "proj" are: ['foo']"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: validate a package from a project for an apptype with it not currently deployed
        Given there is a project with name="proj"
        And there is a package version with version="123"
        And there is a deploy target with name="foo"
        And the deploy target is a part of the project
        When I run "<command> validate proj 123 --apptype foo"
        Then the output is "No deployments to validate for application "proj" in development environment"

        Examples:
            | command |
            | deploy  |
            | config  |

    @wip
    Scenario Outline: validate a package from a project with single apptype
        Given there is a project with name="proj"
        And there is a package version with version="123"
        And there is a deploy target with name="foo"
        And there are hosts:
            | name          |
            | projhost01    |
            | projhost02    |
        And the deploy target is a part of the project
        And the hosts are associated with the deploy target
        And the package version is deployed on the deploy target
        When I run "<command> validate proj 123 --apptype foo"
        Then the output is empty
        And the package version is validated

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: validate a package from a project with single apptype with apptype option
        Given there is a project with name="proj"
        And there is a package version with version="123"
        And there is a deploy target with name="foo"
        And the deploy target is a part of the project
        And the package version is deployed on the deploy target
        When I run "<command> validate proj 123 --apptype foo"
        Then the package version is validated

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: validate a package from a project with multiple apptypes with no options
        Given there is a project with name="proj"
        And there is a package version with version="123"
        And there is a deploy target with name="foo"
        And the deploy target is a part of the project
        And there is a deploy target with name="bar"
        And the deploy target is a part of the project
        And the package version is deployed on the deploy target
        When I run "<command> validate proj 123"
        Then the output is "Application "proj" has multiple corresponding app types, please use "--apptypes" or "--all-apptypes""

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: validate a package from a project with multiple apptypes with apptype option
        Given there is a project with name="proj"
        And there is a package version with version="123"
        And there is a deploy target with name="foo"
        And the deploy target is a part of the project
        And the package version is deployed on the deploy target
        And there is a deploy target with name="bar"
        And the deploy target is a part of the project
        When I run "<command> validate proj 123 --apptype foo"
        Then the package version is validated for deploy target with name="foo"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: validate a package from a project with multiple apptypes with all-apptypes option
        Given there is a project with name="proj"
        And there is a package version with version="123"
        And there is a deploy target with name="foo"
        And there is a deploy target with name="bar"
        And the deploy targets are a part of the project
        And the package version is deployed on the deploy targets
        When I run "<command> validate proj 123 --all-apptypes"
        Then the package version is validated for the deploy targets

        Examples:
            | command |
            | deploy  |
            | config  |
