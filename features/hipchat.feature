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
    Scenario Outline: deploying to multiple hosts of different apptypes
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
        When I run "<command> proj 124 --hosts sprojhost01 sprojhost02 sother01"
        Then there is a hipchat notification with room_id="fakeroom",auth_token="deadbeef"

        Examples:
            | command           |
            | config push       |
            | deploy promote    |
