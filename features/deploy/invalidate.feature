Feature: deploy/config invalidate subcommand
    As a user
    I want to invalidate a package on deploy targets
    So I can prevent the package from being redeployed

    Background:
        Given I have "dev" permissions
        And I am in the "dev" environment

    @no_db
    Scenario Outline: too few arguments
        When I run "<command> invalidate proj"
        Then the output has "usage:"

        Examples:
            | command |
            | deploy  |
            | config  |

    @no_db
    Scenario Outline: too many arguments
        When I run "<command> invalidate proj vers foo"
        Then the output has "usage:"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: invalidate a package from a project that does not exist
        When I run "<command> invalidate proj 567 --all-apptypes"
        Then the output is "Project "proj" does not exist"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: invalidate a package from a project with a version that does not exist
        Given there is a project with name="proj"
        When I run "<command> invalidate proj 123 --all-apptypes"
        Then the output is "Package "proj-name@123" does not exist"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: invalidate a package from a project for an apptype that does not exist
        Given there is a project with name="proj"
        And there is a package version with version="123"
        When I run "<command> invalidate proj 123 --apptype foo"
        Then the output is "Valid apptypes for project "proj" are: []"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: invalidate a package from a project with one of several apptypes that does not exist
        Given there is a project with name="proj"
        And there is a package version with version="123"
        And there is a deploy target with name="foo"
        And the deploy target is a part of the project
        When I run "<command> invalidate proj 123 --apptype foo bar"
        Then the output is "Valid apptypes for project "proj" are: ['foo']"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: invalidate a package from a project for an apptype with it currently deployed
        Given there is a project with name="proj"
        And there is a package version with version="123"
        And there is a deploy target with name="foo"
        And the deploy target is a part of the project
        And the package is deployed on the deploy targets
        When I run "<command> invalidate proj 123 --apptype foo"
        Then the output is "Package "proj-name@123" currently deployed on target "foo""

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: invalidate a package from a project for an apptype
        Given there is a project with name="proj"
        And there is a package version with version="123"
        And there is a deploy target with name="foo"
        And the deploy target is a part of the project
        And the package is deployed on the deploy target
        When I run "<command> invalidate proj 123 --apptype foo"
        Then the output is "Package "proj-name@123" currently deployed on target "foo""

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: invalidate a package from a project with single apptype
        Given there is a project with name="proj"
        And there is a package version with version="123"
        And there is a deploy target with name="foo"
        And the deploy target is a part of the project
        And the package version is deployed on the deploy targets
        And the package version has been validated
        When I run "<command> invalidate proj 123"
        Then the output is empty
        Then the package is invalidated

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: invalidate a package from a project with single apptype with apptype option
        Given there is a project with name="proj"
        And there is a package version with version="123"
        And there is a deploy target with name="foo"
        And the deploy target is a part of the project
        And the package version is deployed on the deploy targets
        And the package version has been validated
        When I run "<command> invalidate proj 123 --apptype foo"
        Then the package is invalidated

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: invalidate a package from a project with multiple apptypes with no options
        Given there is a project with name="proj"
        And there is a package version with version="123"
        And there are deploy targets:
            | name  |
            | foo   |
            | bar   |
        And the deploy targets are a part of the project
        And the package version is deployed on the deploy targets
        And the package version has been validated
        When I run "<command> invalidate proj 123"
        Then the output is "Specify a target constraint (too many targets found: bar, foo)"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: invalidate a package from a project with multiple apptypes with apptype option
        Given there is a project with name="proj"
        And there is a package version with version="123"
        And there are deploy targets:
            | name  |
            | foo   |
            | bar   |
        And the deploy targets are a part of the project
        And the package version is deployed on the deploy targets
        And the package version has been validated
        When I run "<command> invalidate proj 123 --apptype foo"
        Then the package is invalidated for deploy target with name="foo"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: invalidate a package from a project with multiple apptypes with all-apptypes option
        Given there is a project with name="proj"
        And there is a package version with version="123"
        And there are deploy targets:
            | name  |
            | foo   |
            | bar   |
        And the deploy targets are a part of the project
        And the package version is deployed on the deploy targets
        And the package version has been validated
        When I run "<command> invalidate proj 123 --all-apptypes"
        Then the package is invalidated for deploy targets:
            | name  |
            | foo   |
            | bar   |

        Examples:
            | command |
            | deploy  |
            | config  |
