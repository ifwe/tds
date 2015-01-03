Feature: deploy redeploy [DEPRECATED]
    As a developer
    I want to be told the 'deploy redeploy' command is deprecated
    So I can find out about the new 'deploy fix' command

    Scenario: redeploy is deprecated
        Given I have "dev" permissions
        And there is an environment with name="dev"
        And I am in the "dev" environment
        And there is a project with name="proj"
        And there is an application with name="myapp"
        And there is a deploy target with name="the-apptype"
        And the deploy target is a part of the project-application pair
        And there are hosts:
            | name          | env     |
            | dprojhost01   | dev     |
            | dprojhost02   | dev     |
        And the hosts are associated with the deploy target

        And there is a package with version="122"
        And the package is deployed on the deploy targets in the "dev" env
        And the package has been validated in the "development" environment

        And there is a package with version="123"
        And the package is deployed on the deploy targets in the "dev" env
        And the package failed to deploy on the host with name="dprojhost02"

        When I run "deploy redeploy myapp --apptype the-apptype"
        Then the output has "The "redeploy" subcommand has been replaced by "fix".  Please use "tds deploy fix" instead."
