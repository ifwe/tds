Feature: parameter validation (common errors)
    As a developer
    I want to ensure invalid parameter situations are caught
    So I can feel safe and secure

    Background:
        Given I have "dev" permissions
        And there is an environment with name="dev"
        And I am in the "dev" environment

    # NOTE: This test will go away once multiple package definitions
    #       are supported
    Scenario: multiple package definitions found for an application
        Given there is an application with name="myapp",path="app-foo"
        And there is an application with name="myapp",path="app-bar"
        When I run "deploy show myapp"
        Then the output is "Multiple definitions for application found, please file ticket in JIRA for TDS"
