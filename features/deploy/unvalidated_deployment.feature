Feature: attempt promote with unvalidated deployment in previous env
    As a developer
    I want to be notified when I attempt to promote an unvalidated deployment
    So that I don't uninentionally break software in an important env

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
        And there is a package with version="121"
        And the package is deployed on the deploy targets in the "dev" env
        And there are hosts:
            | name          | env   |
            | dprojhost01   | dev   |
            | dprojhost02   | dev   |
            | sprojhost01   | stage |
            | sprojhost02   | stage |
        And the deploy target is a part of the project-application pair
        And the hosts are associated with the deploy target

    Scenario: Attempt promote for a single host
        When I run "deploy promote myapp 121 --hosts sprojhost01"
        Then the output is "Application u'myapp' with version '121' not fully deployed or validated to previous environment (dev) for apptype u'the-apptype'"
