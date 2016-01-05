Feature: Graphite notifications
    As a developer
    I want to send Graphite notifications
    So that I can be a developer, messenger, statistician, and artist all at once

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

    @graphite_server
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
        And graphite notifications are enabled
        When I run "deploy promote myapp 124 --hosts sprojhost01 --detach"
        And I run "deploy promote myapp 124 --hosts sprojhost02 --detach"
        And I run "deploy promote myapp 124 --hosts sother01 --detach"
        Then there are 3 graphite notifications
        And there is a graphite notification containing "tagged.deploy.myapp"
