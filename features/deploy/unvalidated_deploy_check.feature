Feature: check for unvalidated deployments in a given environment
    As an admin
    I want to be notified when unvalidated deployments over a given time are in an environment
    So that I can ensure things are validated

    Background:
        Given I have "dev" permissions
        And there is an environment with name="dev"
        And I am in the "dev" environment
        And email notification is enabled
        And hipchat notifications are enabled
        And there is a project with name="proj"
        And there is an application with name="myapp"
        And there is a deploy target with name="the-apptype"
        And there is a package with version="121"
        And there are hosts:
            | name          | env   |
            | dprojhost01   | dev   |
            | dprojhost02   | dev   |
        And the deploy target is a part of the project-application pair
        And the hosts are associated with the deploy target
        And the package is deployed on the deploy target
        And the package has been validated

    @email_server
    @hipchat_server
    Scenario: No current unvalidated deployments
        Given I wait 3 seconds
        When I run "check"
        Then no email is sent
        And there are 0 hipchat notifications

    @email_server
    @hipchat_server
    Scenario: Current unvalidated deployment
        Given there is a package with version="122"
        And the package is deployed on the deploy target
        And I wait 3 seconds
        When I run "check"
        Then an email is sent with the relevant information for unvalidated="true",apptypes="the-apptype"
        And there is a hipchat notification with room_id="fakeroom",auth_token="deadbeef"
        And a hipchat notification message contains "ATTENTION","myapp+in+development+for+the-apptype+app+tier","Version+122+of+package+myapp","has+not+been+validated"
        And there are 1 hipchat notifications

    @email_server
    @hipchat_server
    Scenario: Unvalidated deployment overridden by a validated deployment
        Given there is a package with version="122"
        And the package is deployed on the deploy target
        And there is a package with version="123"
        And the package is deployed on the deploy target
        And the package has been validated
        And I wait 3 seconds
        When I run "check"
        Then no email is sent
        And there are 0 hipchat notifications

    # TODO: handle edge cases as they occur
