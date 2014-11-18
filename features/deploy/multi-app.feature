Feature: Real-life application usage
    As a user
    I want to have multiple deploy targets with multiple applications
    So that I can have a real live website that's neat

    Background:
        Given I have "dev" permissions
        And I am in the "dev" environment

        And there is a project with name="solr"
        And there is an application with name="solr-app"
        And there are packages:
            | version |
            | 123     |
            | 124     |
            | 125     |
        And there is a deploy target with name="solrsearch"
        And there is a host with name="ss1"
        And the host is associated with the deploy target
        And there is a host with name="ss2"
        And the host is associated with the deploy target
        And there is a host with name="ss3"
        And the host is associated with the deploy target
        And there is an application with name="tagconfig"
        And there are packages:
            | version |
            | 456     |
            | 457     |
            | 458     |
        And there is a deploy target with name="solrbrowse"
        And there is a host with name="sb1"
        And the host is associated with the deploy target
        And there is a host with name="sb2"
        And the host is associated with the deploy target
        And there is a host with name="sb3"
        And the host is associated with the deploy target
        And the deploy targets are a part of the project-application pairs

        And the package with name="tagconfig",version="456" is deployed on the deploy target with name="solrsearch"
        And the package with name="tagconfig",version="457" is deployed on the deploy target with name="solrbrowse"

        And the package with name="solr-app",version="123" is deployed on the deploy target with name="solrsearch"
        And the package with name="solr-app",version="124" is deployed on the deploy target with name="solrbrowse"

    Scenario: other app to deploy target with tagconfig and another app
        When I run "deploy promote solr-app 124 --apptypes solrsearch"
        Then the output has "Completed: 3 out of 3 hosts"
        And package "solr-app" version "124" was deployed to the deploy target with name="solrsearch"

    Scenario: tagconfig to deploy target with tagconfig and another app
        When I run "deploy promote tagconfig 457 --apptypes solrsearch"
        Then the output has "Completed: 3 out of 3 hosts"
        And package "tagconfig" version "457" was deployed to the deploy target with name="solrsearch"

    # TODO: Definitely need more tests here!!!
