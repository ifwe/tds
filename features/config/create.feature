Feature: config create project pkgname pkgpath arch buildhost buildtype [-e|--env-specific]
    As an administrator
    I want to add config projects to the repository
    So that developers can deploy configurations with TDS

    Background:
        Given I have "admin" permissions

    @no_db
    Scenario: too few arguments
        When I run "config create tagconfig pkg pkgpath x86 buildhost"
        Then the output has "usage:"

    @no_db
    Scenario: invalid arguments
        When I run "config create tagconfig pkg pkgpath x86 buildhost buildtype --foo"
        Then the output has "usage:"

    @no_db
    Scenario: adding something with invalid architecture
        When I run "config create tagconfig pkgname /job/pkgname no-exist-arch ci.tagged.com jenkins"
        Then the output has "Invalid architecture: no-exist-arch. Should be one of: i386, noarch, x86_64"

    Scenario: adding a config project
        When I run "config create tagconfig pkgname /job/pkgname noarch ci.tagged.com jenkins"
        Then the output describes a project with name="tagconfig"

    Scenario: adding a config project that already exists
        Given there is a project with name="tagconfig"
        When I run "config create tagconfig pkgname /job/pkgname noarch ci.tagged.com jenkins"
        Then the output has "Project already exists: tagconfig"

    Scenario Outline: With '--env-specific' flag variants
        Given there is a deploy target with name="apptype"
        When I run "config create <flag> tagconfig pkgname /job/pkgname noarch ci.tagged.com jenkins"
        Then the output describes a project with name="tagconfig",env_specific=True

        Examples:
            | flag              |
            | --env-specific    |
            | -e                |

