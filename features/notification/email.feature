Feature: email notifications
    As an administrator
    I want to enable email notifications
    So that developers are notified via email about deployments from TDS

    Background:
        Given I have "dev" permissions
        And I am in the "dev" environment
        And email notification is enabled
        And there is a project with name="proj"
        And there is a deploy target with name="the-apptype"
        And there is a package version with version="123"
        And there are hosts:
            | name          | env   |
            | dprojhost01   | dev   |
            | dprojhost02   | dev   |
        And the deploy target is a part of the project
        And the hosts are associated with the deploy target

    @email_server
    Scenario: deployment occurs with working mail notification
        Given email notification is enabled
        When I run "deploy promote proj 123"
        Then an email is sent with the info deptype="promote",version="123",name="proj-name",apptype="the-apptype",env="dev"

    @email_server
    Scenario: redeploy occurs with working mail notification
        Given email notification is enabled
        And the package version is deployed on the deploy targets in the "dev" env
        And the package version failed to deploy on the host with name="dprojhost02"
        When I run "deploy redeploy proj"
        Then an email is sent with the info deptype="redeploy",version="123",name="proj-name",apptype="the-apptype",env="dev"

    @email_server
    Scenario: rollback occurs with working mail notification
        Given email notification is enabled
        And the package version is deployed on the deploy target
        And the package version has been validated
        And there is a package version with version="124"
        And the package version is deployed on the deploy target
        And the package version has been validated
        When I run "deploy rollback proj"
        Then an email is sent with the info deptype="rollback",version="124",name="proj-name",apptype="the-apptype",env="dev"
