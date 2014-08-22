Feature: deploy/config delete-apptype subcommand
    As an administrator
    I want to remove deploy targets to projects
    So I can stop deploying packages to the targets

    Background:
        Given I have "admin" permissions

    # TODO: should these arg checks be in another file that checks overall
    #       cli behavior?
    @no_db
    Scenario Outline: too few arguments
        When I run "<command> delete-apptype targ"
        Then the output has "usage:"

        Examples:
            | command |
            | deploy  |
            | config  |

    @no_db
    Scenario Outline: too many arguments
        When I run "<command> delete-apptype targ proj foo"
        Then the output has "usage:"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: delete a target that doesn't exist from a project that doesn't exist
        When I run "<command> delete-apptype targ proj"
        Then the output is "Project "proj" does not exist"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: delete a target from a project that doesn't exist
        Given there is a deploy target with name="targ"
        When I run "<command> delete-apptype targ proj"
        Then the output is "Project "proj" does not exist"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: delete a target that doesn't exist from a project
        Given there is a project with name="proj"
        When I run "<command> delete-apptype targ proj"
        Then the output is "Target "targ" does not exist"

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: delete a target from a project
        Given there is a project with name="proj"
        And there is a deploy target with name="targ"
        And the deploy target is a part of the project
        When I run "<command> delete-apptype targ proj"
        Then the output is "Future deployments of "proj" will no longer affect "targ""
        And the deploy target is not a part of the project

        Examples:
            | command |
            | deploy  |
            | config  |

    Scenario Outline: Delete a target from a project again
        Given there is a project with name="proj"
        And there is a deploy target with name="targ"
        And the deploy target is a part of the project
        When I run "<command> delete-apptype targ proj"
        Then the output is "Future deployments of "proj" will no longer affect "targ""

        Examples:
            | command |
            | deploy  |
            | config  |
