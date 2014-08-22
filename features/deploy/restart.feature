Feature: deploy restart subcommand
    As a user
    I want to be able to restart the application on a set of targets
    So I can have changes take effect on those targets

    Background:
        Given I have "dev" permissions
        And I am in the "dev" environment
        And there is a project with name="proj"
        And there is a deploy target with name="appfoo"
        And the deploy target is a part of the project
        And there are hosts:
            | name          |
            | appfoo01      |
            | appfoo02      |
        And the hosts are associated with the deploy target
        And there is a package version with version="123"
        And the package version is deployed on the deploy targets in the "dev" env
        And the package version has been validated in the "development" environment

    Scenario: too few arguments
        When I run "deploy restart"
        Then the output has "usage:"

    Scenario: invalid argument
        When I run "deploy restart proj --foo"
        Then the output has "usage:"

    Scenario: restart a project that doesn't exist
        When I run "deploy restart badproj"
        Then the output is "Project "badproj" does not exist"

    Scenario: restart a project for an apptype that doesn't exist
        When I run "deploy restart proj --apptypes badapp"
        Then the output has "Valid apptypes for project "proj" are: ['appfoo']"

    Scenario: restart a project for several apptypes where one apptype doesn't exist
        When I run "deploy restart proj --apptypes appfoo badapp"
        Then the output has "Valid apptypes for project "proj" are: ['appfoo']"

    Scenario: restart a project for a host that doesn't exist
        When I run "deploy restart proj --hosts badhost"
        Then the output has "These hosts do not exist: badhost"

    Scenario: restart a project for several hosts where one host doesn't exist
        When I run "deploy restart proj --hosts appfoo01 badhost"
        Then the output has "These hosts do not exist: badhost"

    Scenario Outline: restart a project with a single apptype (w/ and w/o option)
        When I run "deploy restart proj <option>"
        Then package "proj-name" was restarted on the deploy target

        Examples:
        | option            |
        |                   |
        | --apptypes appfoo |

    Scenario: restart a project with a multiple apptypes with no option
        Given there is a deploy target with name="appbar"
        And the deploy target is a part of the project
        When I run "deploy restart proj"
        Then the output has "Application "proj" has multiple corresponding app types, please use "--apptypes" or "--all-apptypes""

    Scenario: restart a project with a multiple apptypes with apptypes option
        Given there is a deploy target with name="appbar"
        And the deploy target is a part of the project
        And there is a host with name="appbar01"
        And the host is associated with the deploy target
        When I run "deploy restart proj --apptypes appfoo"
        Then package "proj-name" was restarted on the deploy target with name="appfoo"

    Scenario: restart a project with a multiple apptypes with all-apptypes option
        Given there is a deploy target with name="appbar"
        And the deploy target is a part of the project
        When I run "deploy restart proj --all-apptypes"
        Then package "proj-name" was restarted on the deploy targets

    Scenario: restart a project with a single target in the hosts option
        When I run "deploy restart proj --hosts appfoo01"
        Then package "proj-name" was restarted on the host with name="appfoo01"

    Scenario: restart a project with multiple targets in the hosts option
        When I run "deploy restart proj --hosts appfoo01 appfoo02"
        Then package "proj-name" was restarted on the hosts

    # Note: the delay option actually will wait after the final host as well;
    #       this should probably be fixed (or the behavior changed based on
    #       given situation

    Scenario: restart a project with a valid delay option involving a single target
        When I run "deploy restart proj --delay 10 --hosts appfoo01"
        Then package "proj-name" was restarted on the host with name="appfoo01"

    Scenario: restart a project with an invalid delay option involving a single target
        When I run "deploy restart proj --delay notnum --hosts appfoo01"
        Then the output has "error: argument --delay: invalid int value:"

    Scenario: restart a project with an invalid delay option involving mulitple targets
        When I run "deploy restart proj --delay notnum --apptypes appfoo"
        Then the output has "error: argument --delay: invalid int value:"

    Scenario: restart a project with a valid delay option involving multiple targets
        When I run "deploy restart proj --delay 10 --apptypes appfoo"
        Then package "proj-name" was restarted on the deploy target
        And it took at least 10 seconds

    Scenario: restart a project where at least one of the targets fails when restarting a tier
        Given the host "appfoo01" will fail to restart
        When I run "deploy restart proj"
        Then the output has "Some hosts had failures"

    Scenario: restart a project where at least one of the targets fails when restarting a target or targets
        Given the host "appfoo01" will fail to restart
        When I run "deploy restart proj --hosts appfoo01 appfoo02"
        Then the output has "Some hosts had failures"
