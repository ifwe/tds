Feature: package add subcommand
    As a user
    I want to add a specific version of a package
    So I can deploy that version of that package to targets

    Background:
        Given I have "dev" permissions
        And I am in the "dev" environment

    @no_db
    Scenario: too few arguments
        When I run "package add proj job"
        Then the output has "usage:"

    @no_db
    Scenario: too many arguments
        When I run "package add proj job vers foo"
        Then the output has "usage:"

    Scenario: add a package to a project that doesn't exist
        When I run "package add proj job 123"
        Then the output is "Project "proj" does not exist"

    @jenkins_server
    Scenario: add a package to a project with a job name that doesn't exist
        Given there is a project with name="proj"
        When I run "package add proj job 123"
        Then the output has "Job "job" not found"

    @jenkins_server
    Scenario: add a package to a project with a version that doesn't exist
        Given there is a project with name="proj"
        And there is a jenkins job with name="job"
        When I run "package add proj job 123"
        Then the output has "Build "job@123" does not exist on"

    @jenkins_server
    Scenario: add a package to a project
        Given there is a project with name="proj"
        And there is a jenkins job with name="job"
        And the job has a build with number="123"
        When I start to run "package add proj job 123"
        And I wait 10 seconds
        And the status is changed to "completed" for package with name="proj-name",version=123
        And the command finishes
        Then the output has "Added package version: "proj-name@123""

    @jenkins_server
    Scenario: add a package to a project again
        Given there is a project with name="proj"
        And there is a package version with version="123"
        And there is a jenkins job with name="job"
        And the job has a build with number="123"
        When I run "package add proj job 123"
        Then the output has "Package version "proj-name@123" already exists"

    @jenkins_server
    Scenario: add a package to a project where actual package isn't available
        Given there is a project with name="proj"
        And there is a jenkins job with name="job"
        And the job has a build with number="123"
        And jenkins does not have the job's artifact
        When I run "package add proj job 123"
        Then the output has "Artifact not found for "job@123" on"

    @jenkins_server
    Scenario: add a package to a project where repo update daemon fails to return in time
        Given there is a project with name="proj"
        And there is a jenkins job with name="job"
        And the job has a build with number="123"
        When I start to run "package add proj job 123"
        And I wait 16 seconds
        And the command finishes
        Then the output has "Please open a JIRA issue in the TDS project."

     # TODO: There are probably more failure tests that can be written here!
