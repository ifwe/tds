Feature: deploy/config add-apptype subcommand
    As an administrator
    I want to add deploy targets to projects
    So I can deploy packages to the targets

    Background:
        Given I have "admin" permissions

    # TODO: should these arg checks be in another file that checks overall
    #       cli behavior?
    @no_db
    Scenario Outline: too few arguments
        When I run "<command> add-apptype targ"
        Then the output has "usage:"

        Examples:
            | command |
            | deploy  |
            | config  |

    @no_db
    Scenario Outline: too many arguments
        When I run "<command> add-apptype targ proj foo"
        Then the output has "usage:"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: add a target that doesn't exist to a project that doesn't exist
        When I run "<command> add-apptype targ proj"
        Then the output is "Project "proj" does not exist"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: add a target to a project that doesn't exist
        Given there is a deploy target with name="targ"
        When I run "<command> add-apptype targ proj"
        Then the output is "Project "proj" does not exist"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: add a target that doesn't exist to a project
        Given there is a project with name="proj"
        When I run "<command> add-apptype targ proj"
        Then the output is "Deploy target does not exist: targ"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: add a target to a project
        Given there is a project with name="proj"
        And there is a deploy target with name="targ"
        When I run "<command> add-apptype targ proj"
        Then the output is "Future deployments of "proj" will affect "targ""
        And the deploy target is a part of the project

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: add a target to a project again
        Given there is a project with name="proj"
        And there is a deploy target with name="targ"
        And the deploy target is a part of the project
        When I run "<command> add-apptype targ proj"
        Then the output is ""targ" is already a part of "proj""

        Examples:
            | command |
            | deploy  |
            | config  |
