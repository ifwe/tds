Feature: repository add project pkgname pkgpath arch buildhost buildtype apptypes [-e|--env-specific] [-c|--config]
    As an administrator
    I want to add projects to the repository
    So that developers can deploy the projects with TDS

    Background:
        Given I have "admin" permissions

    @no_db
    Scenario: too few arguments
        When I run "repository add proj pkg pkgpath x86 buildhost buildtype"
        Then the output has "usage:"

    @no_db
    Scenario: invalid arguments
        When I run "repository add proj pkg pkgpath x86 buildhost buildtype apptypes --foo"
        Then the output has "usage:"

    Scenario: adding something with invalid architecture
        Given there is a deploy target with name="apptype"
        When I run "repository add proj pkgname /job/pkgname no-exist-arch ci.tagged.com jenkins apptype"
        Then the output has "Invalid architecture: no-exist-arch. Should be one of: i386, noarch, x86_64"

    Scenario: adding to an existing apptype
        Given there is a deploy target with name="apptype"
        When I run "repository add proj pkgname /job/pkgname noarch ci.tagged.com jenkins apptype"
        Then the output describes a project with name="proj",apptype="apptype"

    Scenario: Add to multiple apptypes
        Given there is a deploy target with name="apptype1"
        And there is a deploy target with name="apptype2"
        When I run "repository add proj pkgname /job/pkgname noarch ci.tagged.com jenkins apptype1 apptype2"
        Then the output describes a project with name="proj",apptype="apptype1",apptype="apptype2"

    Scenario: Add to an apptype that does not exist
        When I run "repository add proj pkgname /job/pkgname noarch ci.tagged.com jenkins apptype"
        Then the output has "Apptype 'apptype' does not exist"

    Scenario: Add to multiple apptypes, with one that does not exist
        Given there is a deploy target with name="apptype1"
        When I run "repository add proj pkgname /job/pkgname noarch ci.tagged.com jenkins apptype1 apptype2"
        Then the output has "Apptype 'apptype2' does not exist"

    Scenario Outline: With '--env-specific' flag variants
        Given there is a deploy target with name="apptype"
        When I run "repository add <flag> proj pkgname /job/pkgname noarch ci.tagged.com jenkins apptype"
        Then the output describes a project with name="proj",env_specific=True

        Examples:
            | flag              |
            | --env-specific    |
            | -e                |

    Scenario Outline: With '--config' flag variants
        Given there is a deploy target with name="apptype"
        And there is a project with name="tagconfig"
        When I run "repository add proj pkgname /job/pkgname noarch ci.tagged.com jenkins apptype <flag> tagconfig"
        Then the output describes a project with name="proj",apptype="apptype",package="pkgname"
        # TODO: output should also have package="tagconfig"

        Examples:
            | flag      |
            | --config  |
            | -c        |
