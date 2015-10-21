Feature: Ongoing deployments blocking attempted new ones
    As a developer
    I don't want to clobber ongoing deployments
    So that there's less violence in the world

    Background:
        Given there are environments
            | name   |
            | dev    |
            | stage  |

    Scenario Outline: promote with ongoing apptype deployment
        Given I have "dev" permissions
        And I am in the "dev" environment
        And there is a project with name="proj"
        And there is an application with name="myapp"
        And there is a deploy target with name="the-apptype"
        And there is a package with version="123"
        And there are hosts:
            | name          | env   |
            | dprojhost01   | dev   |
            | dprojhost02   | dev   |
        And the deploy target is a part of the project-application pair
        And the hosts are associated with the deploy target
        And there is an ongoing deployment on the deploy target
        When I run "deploy promote myapp 123 <targets>"
        Then the output has "currently running a deployment for the the-apptype app tier in the development environment, skipping..."

    Examples:
        | targets                   |
        | --hosts dprojhost01       |
        | --all-apptypes            |
        | --apptypes the-apptype    |

    Scenario Outline: promote with ongoing host deployment
        Given I have "dev" permissions
        And I am in the "dev" environment
        And there is a project with name="proj"
        And there is an application with name="myapp"
        And there is a deploy target with name="the-apptype"
        And there is a package with version="123"
        And there are hosts:
            | name          | env   |
            | dprojhost01   | dev   |
            | dprojhost02   | dev   |
        And the deploy target is a part of the project-application pair
        And the hosts are associated with the deploy target
        And there is an ongoing deployment on the hosts="dprojhost01"
        When I run "deploy promote myapp 123 <targets>"
        Then the output has "currently running a deployment for the hosts "dprojhost01" in the development environment, skipping..."

    Examples:
        | targets                   |
        | --hosts dprojhost01       |
        | --all-apptypes            |
        | --apptypes the-apptype    |

    Scenario: promote with ongoing host deployment
        Given I have "dev" permissions
        And I am in the "dev" environment
        And there is a project with name="proj"
        And there is an application with name="myapp"
        And there is a deploy target with name="the-apptype"
        And there is a package with version="123"
        And there are hosts:
            | name          | env   |
            | dprojhost01   | dev   |
            | dprojhost02   | dev   |
        And the deploy target is a part of the project-application pair
        And the hosts are associated with the deploy target
        And there is an ongoing deployment on the hosts="dprojhost01"
        When I run "deploy promote myapp 123 --hosts dprojhost02"
        Then the output has "Completed: 1 out of 1 hosts"

    Scenario Outline: fix with ongoing apptype deployment
        Given I have "stage" permissions
        And I am in the "stage" environment
        And there is a project with name="proj"
        And there is an application with name="myapp"
        And there is a deploy target with name="the-apptype"
        And the deploy target is a part of the project-application pair
        And there are hosts:
            | name          | env     |
            | dprojhost01   | dev     |
            | dprojhost02   | dev     |
            | sprojhost01   | stage   |
            | sprojhost02   | stage   |
        And the hosts are associated with the deploy target

        And there is a package with version="122"
        And the package is deployed on the deploy targets in the "stage" env
        And the package has been validated in the "staging" environment

        And there is a package with version="123"
        And the package is deployed on the deploy targets in the "dev" env
        And the package has been validated in the "development" environment
        And the package is deployed on the deploy targets in the "stage" env
        And there is an ongoing deployment on the deploy target
        When I run "deploy fix myapp <targets>"
        Then the output has "currently running a deployment for the the-apptype app tier in the staging environment, skipping..."

    Examples:
        | targets                   |
        | --hosts sprojhost02       |
        | --all-apptypes            |
        | --apptypes the-apptype    |
