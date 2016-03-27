Feature: package add display output
    As a developer
    I want to be given information on the status of a package add
    So that I can be aware and invested in my work

    Background:
        Given there is an environment with name="dev"
        And I have "dev" permissions
        And I am in the "dev" environment
        And there is an application with name="myapp"
        And there is a jenkins job with name="job"
        And the job has a build with number="123"

    @jenkins_server
    Scenario: add a package
        When I start to run "package add myapp 123"
        And I wait 10 seconds
        And the status of the package with version="123" changes to "processing"
        And I wait 2 seconds
        And the status of the package with version="123" changes to "completed"
        And I wait 2 seconds
        And the command finishes
        Then the output has "Package now being added, press Ctrl-C at any time to detach session..."
        And the output has "Status:		[processing]"
        And the output has "Status:		[completed]"

    @jenkins_server
    Scenario: add a package with a failure
        When I start to run "package add myapp 123"
        And I wait 10 seconds
        And the status of the package with version="123" changes to "processing"
        And I wait 2 seconds
        And the status of the package with version="123" changes to "failed"
        And I wait 2 seconds
        And the command finishes
        Then the output has "Package now being added, press Ctrl-C at any time to detach session..."
        And the output has "Status:		[processing]"
        And the output has "Status:		[failed]"
