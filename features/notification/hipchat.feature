Feature: HipChat notifications
    As a developer
    I want to send HipChat notifications
    So that I can better collaborate with other developers

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
        And there is a package with version="123"
        And the package is deployed on the deploy targets in the "dev" env
        And the package has been validated in the "development" environment
        And there are hosts:
            | name          | env   |
            | dprojhost01   | dev   |
            | dprojhost02   | dev   |
            | sprojhost01   | stage |
            | sprojhost02   | stage |
        And the deploy target is a part of the project-application pair
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
        And the deploy target is a part of the project-application pair
        And there is a package with version="124"
        And the package is deployed on the deploy targets in the "dev" env
        And the package has been validated in the "development" environment
        And hipchat notifications are enabled
        When I run "deploy promote myapp 124 --hosts sprojhost01 --detach"
        And I run "deploy promote myapp 124 --hosts sprojhost02 --detach"
        And I run "deploy promote myapp 124 --hosts sother01 --detach"
        Then there was a hipchat notification with room_id="fakeroom",auth_token="deadbeef"
        And a hipchat notification message contains "promote","of+version+124+of+myapp+on+hosts+sprojhost01"
        And there are 3 hipchat notifications

    @hipchat_server
    Scenario: deploying to all apptypes
        Given there is a package with version="124"
        And the package is deployed on the deploy targets in the "dev" env
        And the package has been validated in the "development" environment
        And hipchat notifications are enabled
        When I run "deploy promote myapp 124 --all-apptypes --detach"
        Then there was a hipchat notification with room_id="fakeroom",auth_token="deadbeef"
        And a hipchat notification message contains "promote","of+version+124+of+myapp+on+app+tier","the-apptype+in+stage"
        And there are 1 hipchat notifications

    @hipchat_server
    Scenario: deploying to specific apptypes
        Given there is a package with version="124"
        And the package is deployed on the deploy targets in the "dev" env
        And the package has been validated in the "development" environment
        And hipchat notifications are enabled
        When I run "deploy promote myapp 124 --apptypes the-apptype --detach"
        Then there was a hipchat notification with room_id="fakeroom",auth_token="deadbeef"
        And a hipchat notification message contains "promote","of+version+124+of+myapp+on+app+tier","the-apptype+in+stage"
        And there are 1 hipchat notifications

    @hipchat_server
    Scenario: fix on all apptypes
        Given there is a deploy target with name="another-apptype"
        And there is a host with name="anotherhost01"
        And the host is associated with the deploy target
        And the deploy target is a part of the project-application pair
        And the package is deployed on the deploy target
        And the package failed to deploy on the host with name="anotherhost01"
        And hipchat notifications are enabled
        When I run "deploy fix myapp --all-apptypes --detach"
        Then there was a hipchat notification with room_id="fakeroom",auth_token="deadbeef"
        And a hipchat notification message contains "fix","of+version+123+of+myapp+on+app+tier","another-apptype","in+stage"
        And there are 1 hipchat notifications

    @hipchat_server
    Scenario: fix on specific apptypes
        Given there is a deploy target with name="another-apptype"
        And there is a host with name="anotherhost01"
        And the host is associated with the deploy target
        And the deploy target is a part of the project-application pair
        And the package is deployed on the deploy target
        And the package failed to deploy on the host with name="anotherhost01"
        And hipchat notifications are enabled
        When I run "deploy fix myapp --apptypes another-apptype --detach"
        Then there was a hipchat notification with room_id="fakeroom",auth_token="deadbeef"
        And a hipchat notification message contains "fix","of+version+123+of+myapp+on+app+tier","another-apptype","in+stage"
        And there are 1 hipchat notifications

    @hipchat_server
    Scenario: fix on specific host
        Given there is a deploy target with name="another-apptype"
        And there is a host with name="anotherhost01"
        And the host is associated with the deploy target
        And the deploy target is a part of the project-application pair
        And the package is deployed on the deploy target
        And the package failed to deploy on the host with name="anotherhost01"
        And hipchat notifications are enabled
        When I run "deploy fix myapp --hosts anotherhost01 --detach"
        Then there was a hipchat notification with room_id="fakeroom",auth_token="deadbeef"
        And a hipchat notification message contains "fix","of+version+123+of+myapp+on+hosts+anotherhost01","in+stage"
        And there are 1 hipchat notifications

    @hipchat_server
    Scenario: rollback version on apptype
        Given the package is deployed on the deploy target
        And the package has been validated

        And I wait 1 seconds
        And there is a package with version="121"
        And the package is deployed on the deploy target
        And the package has been validated

        And I wait 1 seconds
        And there is a package with version="122"
        And the package is deployed on the deploy target
        And the package has been invalidated

        And hipchat notifications are enabled

        When I run "deploy rollback myapp --apptype the-apptype --detach"
        Then there was a hipchat notification with room_id="fakeroom",auth_token="deadbeef"
        And a hipchat notification message contains "rollback","of+version+121+of+myapp+on+app+tier","the-apptype","in+stage"
        And there are 1 hipchat notifications

    @hipchat_server
    Scenario: rollback version on all apptypes
        Given the package is deployed on the deploy target
        And the package has been validated

        And I wait 1 seconds
        And there is a package with version="121"
        And the package is deployed on the deploy target
        And the package has been validated

        And I wait 1 seconds
        And there is a package with version="122"
        And the package is deployed on the deploy target
        And the package has been invalidated

        And hipchat notifications are enabled

        When I run "deploy rollback myapp --all-apptypes --detach"
        Then there was a hipchat notification with room_id="fakeroom",auth_token="deadbeef"
        And a hipchat notification message contains "rollback","of+version+121+of+myapp+on+app+tier","the-apptype","in+stage"
        And there are 1 hipchat notifications

    @hipchat_server
    Scenario: rollback version on specific host
        Given the package is deployed on the deploy target
        And the package has been validated

        And I wait 1 seconds
        And there is a package with version="124"
        And the package is deployed on the deploy target
        And the package has been validated

        And I wait 1 seconds
        And there is a package with version="125"
        And the package is deployed on the deploy target
        And the package has been invalidated

        And hipchat notifications are enabled

        When I run "deploy rollback myapp --hosts sprojhost01 --detach"
        Then there was a hipchat notification with room_id="fakeroom",auth_token="deadbeef"
        And a hipchat notification message contains "rollback","of+version+124+of+myapp+on+hosts","sprojhost01","in+stage"
        And there are 1 hipchat notifications

    @hipchat_server
    Scenario: hipchat server failure
        Given the package is deployed on the deploy target
        And the package has been validated

        And I wait 1 seconds
        And there is a package with version="200"
        And the package is deployed on the deploy target
        And the package has been validated

        And I wait 1 seconds
        And there is a package with version="201"
        And the package is deployed on the deploy target
        And the package has been invalidated

        And hipchat notifications are enabled

        When I run "deploy rollback myapp --hosts sprojhost01 --detach"
        Then there is a hipchat failure
        And the output has "Deployment was successful. However, notification to HipChat failed, status code is: 403"

    @hipchat_server
    Scenario: no hipchat response
        Given there is a package with version="500"
        And the package is deployed on the deploy targets in the "dev" env
        And the package has been validated in the "development" environment

        And hipchat notifications are enabled

        When I run "deploy promote myapp 500 --all-apptypes --detach"
        Then the output has "Deployment was successful. However, notification to HipChat failed, message is: "
