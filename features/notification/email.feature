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
        And there is a package with version="123"
        And there are hosts:
            | name          | env   |
            | dprojhost01   | dev   |
            | dprojhost02   | dev   |
        And the deploy target is a part of the project-application pair
        And the hosts are associated with the deploy target
        And there is a deploy target with name="another-apptype"
        And there are hosts:
            | name            | env   |
            | danotherhost01  | dev   |
            | danotherhost02  | dev   |
        And the deploy target is a part of the project-application pair
        And the hosts are associated with the deploy target

    @email_server
    Scenario: deployment of single apptype occurs with working mail notification
        Given email notification is enabled
        When I run "deploy promote proj 123 --apptypes the-apptype"
        Then an email is sent with the relevant information for deptype="promote",apptypes="the-apptype"

    @email_server
    Scenario: deployment of all apptypes occurs with working mail notification
        Given email notification is enabled
        When I run "deploy promote proj 123 --all-apptypes"
        Then an email is sent with the relevant information for deptype="promote",apptypes="the-apptype:another-apptype"

    @email_server
    Scenario: deployment of a host(s) occurs with working mail notification
        Given email notification is enabled
        When I run "deploy promote proj 123 --hosts dprojhost01 danotherhost01"
        Then an email is sent with the relevant information for deptype="promote",hosts="dprojhost01:danotherhost01"

    @email_server
    Scenario: redeploy of single apptype occurs with working mail notification
        Given email notification is enabled
        And the package is deployed on the deploy targets in the "dev" env
        And the package failed to deploy on the host with name="dprojhost02"
        When I run "deploy redeploy proj --apptypes the-apptype"
        Then an email is sent with the relevant information for deptype="redeploy",apptypes="the-apptype"

    @email_server
    Scenario: redeploy of all apptypes occurs with working mail notification
        Given email notification is enabled
        And the package is deployed on the deploy targets in the "dev" env
        And the package failed to deploy on the host with name="dprojhost02"
        When I run "deploy redeploy proj --all-apptypes"
        Then an email is sent with the relevant information for deptype="redeploy",apptypes="the-apptype:another-apptype"

    @email_server
    Scenario: redeploy of a host(s) occurs with working mail notification
        Given email notification is enabled
        And the package is deployed on the deploy targets in the "dev" env
        And the package failed to deploy on the host with name="dprojhost02"
        When I run "deploy redeploy proj --hosts dprojhost02"
        Then an email is sent with the relevant information for deptype="redeploy",hosts="dprojhost02"

    @email_server
    Scenario: rollback of single apptype occurs with working mail notification
        Given email notification is enabled
        And the package is deployed on the deploy targets
        And the package has been validated
        And there is a package with version="124"
        And the package is deployed on the deploy targets
        And the package has been validated
        When I run "deploy rollback proj --apptypes the-apptype"
        Then an email is sent with the relevant information for deptype="rollback",apptypes="the-apptype"

    @email_server
    Scenario: rollback of all apptypes occurs with working mail notification
        Given email notification is enabled
        And the package is deployed on the deploy targets
        And the package has been validated
        And there is a package with version="124"
        And the package is deployed on the deploy targets
        And the package has been validated
        When I run "deploy rollback proj --all-apptypes"
        Then an email is sent with the relevant information for deptype="rollback",apptypes="the-apptype:another-apptype"

    @email_server
    Scenario: rollback of a host(s) occurs with a working mail notification
        Given email notification is enabled
        And the package is deployed on the deploy targets
        And the package has been validated
        And there is a package with version="124"
        And the package is deployed on the deploy targets
        When I run "deploy rollback proj --hosts dprojhost01 danotherhost01"
        Then an email is sent with the relevant information for deptype="rollback",hosts="dprojhost01:danotherhost01"

    @email_server
    Scenario: email server fails while notification attempted
        Given email notification is enabled
        And the email server is broken
        When I run "deploy promote proj 123 --apptypes the-apptype"
        Then there is a failure message for the email send
