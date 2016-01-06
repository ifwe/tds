Feature: deploy display output
    As a developer
    I want to be given information on the status of a deployment as it is carried out by the daemon
    So that I can be aware and invested in my deployment

    Background:
        Given I have "stage" permissions
        And there are environments
            | name   |
            | dev    |
            | stage  |
        And I am in the "stage" environment
        And there is a project with name="proj"
        And there is an application with name="myapp"
        And there is a deploy target with name="the-apptype"
        And there are packages:
            | version   | revision  |
            | 121       | 1         |
            | 122       | 1         |
            | 123       | 1         |
        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | complete  |
            | 2     | foo   | complete  |
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status    | user  | app_id    | package_id    |
            | 1     | 1             | 1                 | validated | foo   | 2         | 1             |
        And I wait 1 seconds
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status    | user  | app_id    | package_id    |
            | 2     | 2             | 2                 | validated | foo   | 2         | 2             |
        And I wait 1 seconds
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status    | user  | app_id    | package_id    |
            | 3     | 1             | 1                 | validated | foo   | 2         | 3             |
        And there are hosts:
            | name          | env   | app_id    |
            | dprojhost01   | dev   | 2         |
            | dprojhost02   | dev   | 2         |
            | sprojhost01   | stage | 2         |
            | sprojhost02   | stage | 2         |
        And the tier "the-apptype" is associated with the application "myapp" for the project "proj"

    Scenario: promote version to hosts
        When I start to run "deploy promote myapp 123 --hosts sprojhost01 sprojhost02"
        And I wait 10 seconds
        And the status of the host deployment with deployment_id=3,host_id=3 changes to "inprogress"
        And I wait 2 seconds
        And the status of the host deployment with deployment_id=3,host_id=3 changes to "ok"
        And I wait 2 seconds
        And the status of the host deployment with deployment_id=3,host_id=4 changes to "inprogress"
        And I wait 2 seconds
        And the status of the host deployment with deployment_id=3,host_id=4 changes to "ok"
        And the status of the deployment with id=3 changes to "complete"
        And I wait 2 seconds
        And the command finishes
        Then the output has "Deployment now being run, press Ctrl-C at any time to cancel..."
        And the output has "sprojhost01:		[inprogress]"
        And the output has "sprojhost01:		[ok]"
        And the output has "sprojhost02:		[inprogress]"
        And the output has "sprojhost02:		[ok]"
        And the output has "Deployment:	[complete]"

    Scenario: promote version to hosts with a failure
        When I start to run "deploy promote myapp 123 --hosts sprojhost01 sprojhost02"
        And I wait 10 seconds
        And the status of the host deployment with deployment_id=3,host_id=3 changes to "inprogress"
        And I wait 2 seconds
        And the status of the host deployment with deployment_id=3,host_id=3 changes to "failed"
        And I wait 2 seconds
        And the status of the host deployment with deployment_id=3,host_id=4 changes to "inprogress"
        And I wait 2 seconds
        And the status of the host deployment with deployment_id=3,host_id=4 changes to "ok"
        And the status of the deployment with id=3 changes to "failed"
        And I wait 2 seconds
        And the command finishes
        Then the output has "Deployment now being run, press Ctrl-C at any time to cancel..."
        And the output has "sprojhost01:		[inprogress]"
        And the output has "sprojhost01:		[failed]"
        And the output has "sprojhost02:		[inprogress]"
        And the output has "sprojhost02:		[ok]"
        And the output has "Deployment:	[failed]"

    Scenario: promote version to apptype
        When I start to run "deploy promote myapp 123 --apptype the-apptype"
        And I wait 10 seconds
        And the status of the tier deployment with deployment_id=3,app_id=2 changes to "inprogress"
        And the status of the host deployment with deployment_id=3,host_id=3 changes to "inprogress"
        And I wait 2 seconds
        And the status of the host deployment with deployment_id=3,host_id=3 changes to "ok"
        And the status of the host deployment with deployment_id=3,host_id=4 changes to "inprogress"
        And I wait 2 seconds
        And the status of the host deployment with deployment_id=3,host_id=4 changes to "ok"
        And the status of the tier deployment with deployment_id=3,app_id=2 changes to "complete"
        And the status of the deployment with id=3 changes to "complete"
        And I wait 2 seconds
        And the command finishes
        Then the output has "Deployment now being run, press Ctrl-C at any time to cancel..."
        And the output has "the-apptype:		[inprogress]"
        And the output has "	sprojhost01:	[inprogress]"
        And the output has "	sprojhost01:	[ok]"
        And the output has "	sprojhost02:	[inprogress]"
        And the output has "	sprojhost02:	[ok]"
        And the output has "the-apptype:		[complete]"
        And the output has "Deployment:	[complete]"

    Scenario: promote version to apptype with a failure
        When I start to run "deploy promote myapp 123 --apptype the-apptype"
        And I wait 10 seconds
        And the status of the tier deployment with deployment_id=3,app_id=2 changes to "inprogress"
        And the status of the host deployment with deployment_id=3,host_id=3 changes to "inprogress"
        And I wait 2 seconds
        And the status of the host deployment with deployment_id=3,host_id=3 changes to "failed"
        And the status of the host deployment with deployment_id=3,host_id=4 changes to "inprogress"
        And I wait 2 seconds
        And the status of the host deployment with deployment_id=3,host_id=4 changes to "ok"
        And the status of the tier deployment with deployment_id=3,app_id=2 changes to "incomplete"
        And the status of the deployment with id=3 changes to "failed"
        And I wait 2 seconds
        And the command finishes
        Then the output has "Deployment now being run, press Ctrl-C at any time to cancel..."
        And the output has "the-apptype:		[inprogress]"
        And the output has "	sprojhost01:	[inprogress]"
        And the output has "	sprojhost01:	[failed]"
        And the output has "	sprojhost02:	[inprogress]"
        And the output has "	sprojhost02:	[ok]"
        And the output has "the-apptype:		[incomplete]"
        And the output has "Deployment:	[failed]"
