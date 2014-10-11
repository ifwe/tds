Feature: HipChat notifications
    As a developer
    I want to send HipChat notifications
    So that I can better collaborate with other developers

    Background:
        Given I have "stage" permissions
        And I am in the "stage" environment
        And there is a project with name="proj"
        And there is a deploy target with name="the-apptype"
        And there is a package version with version="123"
        And the package version is deployed on the deploy targets in the "dev" env
        And the package version has been validated in the "development" environment
        And there are hosts:
            | name          | env   |
            | dprojhost01   | dev   |
            | dprojhost02   | dev   |
            | sprojhost01   | stage |
            | sprojhost02   | stage |
        And the deploy target is a part of the project
        And the hosts are associated with the deploy target

    @hipchat_server
    Scenario: deploying to multiple hosts of different apptypes
        Given there is a deploy target with name="other-apptype"
        And there are hosts:
            | name       | env    |
            | dother01   | dev    |
            | dother02   | dev    |
            | sother01   | stage  |
            | sother02   | stage  |
        And the hosts are associated with the deploy target
        And the deploy target is a part of the project
        And there is a package version with version="124"
        And the package version is deployed on the deploy targets in the "dev" env
        And the package version has been validated in the "development" environment
        And hipchat notifications are enabled
        When I run "deploy promote proj 124 --hosts sprojhost01"
        And I run "deploy promote proj 124 --hosts sprojhost02"
        And I run "deploy promote proj 124 --hosts sother01"
        Then there is a hipchat notification with room_id="fakeroom",auth_token="deadbeef"
        And a hipchat notification message contains "promote","of+version+124+of+proj-name+on+hosts+sprojhost01"
        And there are 3 hipchat notifications

    @hipchat_server
    Scenario: deploying to all apptypes
        Given there is a package version with version="124"
        And the package version is deployed on the deploy targets in the "dev" env
        And the package version has been validated in the "development" environment
        And hipchat notifications are enabled
        When I run "deploy promote proj 124 --all-apptypes"
        Then there is a hipchat notification with room_id="fakeroom",auth_token="deadbeef"
        And a hipchat notification message contains "promote","of+version+124+of+proj-name+on+app+tier","the-apptype+in+stage"
        And there are 1 hipchat notifications

    @hipchat_server
    Scenario: deploying to specific apptypes
        Given there is a package version with version="124"
        And the package version is deployed on the deploy targets in the "dev" env
        And the package version has been validated in the "development" environment
        And hipchat notifications are enabled
        When I run "deploy promote proj 124 --apptypes the-apptype"
        Then there is a hipchat notification with room_id="fakeroom",auth_token="deadbeef"
        And a hipchat notification message contains "promote","of+version+124+of+proj-name+on+app+tier","the-apptype+in+stage"
        And there are 1 hipchat notifications

    @hipchat_server
    Scenario: redeploy to all apptypes
        Given there is a deploy target with name="another-apptype"
        And there is a host with name="anotherhost01"
        And the host is associated with the deploy target
        And the deploy target is a part of the project
        And the package version is deployed on the deploy target
        And the package version failed to deploy on the host with name="anotherhost01"
        And hipchat notifications are enabled
        When I run "deploy redeploy proj --all-apptypes"
        Then there is a hipchat notification with room_id="fakeroom",auth_token="deadbeef"
        And a hipchat notification message contains "redeploy","of+version","+on+app+tier","the-apptype","another-apptype","in+stage"
        And there are 1 hipchat notifications

    @hipchat_server
    Scenario: redeploy to specific apptypes
        Given there is a deploy target with name="another-apptype"
        And there is a host with name="anotherhost01"
        And the host is associated with the deploy target
        And the deploy target is a part of the project
        And the package version is deployed on the deploy target
        And the package version failed to deploy on the host with name="anotherhost01"
        And hipchat notifications are enabled
        When I run "deploy redeploy proj --apptypes another-apptype"
        Then there is a hipchat notification with room_id="fakeroom",auth_token="deadbeef"
        And a hipchat notification message contains "redeploy","of+version","+on+app+tier","another-apptype","in+stage"
        And there are 1 hipchat notifications

    @hipchat_server
    Scenario: redeploy to specific host
        Given there is a deploy target with name="another-apptype"
        And there is a host with name="anotherhost01"
        And the host is associated with the deploy target
        And the deploy target is a part of the project
        And the package version is deployed on the deploy target
        And the package version failed to deploy on the host with name="anotherhost01"
        And hipchat notifications are enabled
        When I run "deploy redeploy proj --hosts anotherhost01"
        Then there is a hipchat notification with room_id="fakeroom",auth_token="deadbeef"
        And a hipchat notification message contains "redeploy","of+version","on+hosts+anotherhost01","in+stage"
        And there are 1 hipchat notifications

    @hipchat_server
    Scenario: rollback version to apptype
        Given the package version is deployed on the deploy target
        And the package version has been validated

        And there is a package version with version="121"
        And the package version is deployed on the deploy target
        And the package version has been validated

        And there is a package version with version="122"
        And the package version is deployed on the deploy target
        And the package version has been invalidated

        And hipchat notifications are enabled

        When I run "deploy rollback proj --apptype the-apptype"
        Then there is a hipchat notification with room_id="fakeroom",auth_token="deadbeef"
        And a hipchat notification message contains "rollback","of+version","app+tier","the-apptype","in+stage"
        And there are 1 hipchat notifications

    @hipchat_server
    Scenario: rollback version to all apptypes
        Given the package version is deployed on the deploy target
        And the package version has been validated

        And there is a package version with version="121"
        And the package version is deployed on the deploy target
        And the package version has been validated

        And there is a package version with version="122"
        And the package version is deployed on the deploy target
        And the package version has been invalidated

        And hipchat notifications are enabled

        When I run "deploy rollback proj --all-apptypes"
        Then there is a hipchat notification with room_id="fakeroom",auth_token="deadbeef"
        And a hipchat notification message contains "rollback","of+version","app+tier","the-apptype","in+stage"
        And there are 1 hipchat notifications

    @hipchat_server
    Scenario: rollback version to specific host
        Given the package version is deployed on the deploy target
        And the package version has been validated

        And there is a package version with version="121"
        And the package version is deployed on the deploy target
        And the package version has been validated

        And there is a package version with version="122"
        And the package version is deployed on the deploy target
        And the package version has been invalidated

        And hipchat notifications are enabled

        When I run "deploy rollback proj --hosts sprojhost01"
        Then there is a hipchat notification with room_id="fakeroom",auth_token="deadbeef"
        And a hipchat notification message contains "rollback","of+version","sprojhost01","in+stage"
        And there are 1 hipchat notifications
