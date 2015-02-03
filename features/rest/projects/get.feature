Feature: GET project(s) from the REST API
    As a developer
    I want information on projects
    So that I can be informed of the current state of the database

    @rest
    Scenario: no projects
        When I query GET "/projects"
        Then the response code is 200
        And the response contains a list of 0 items

    @rest
    Scenario: get all projects
        Given there are projects:
            | name  |
            | proj1 |
            | proj2 |
            | proj3 |
        When I query GET "/projects"
        Then the response code is 200
        And the response contains a list of 3 items
        And the response contains a project with name="proj1"
        And the response contains a project with name="proj2"
        And the response contains a project with name="proj3"

    @rest
    Scenario Outline: get a single project
        Given there are projects:
            | name  |
            | proj1 |
            | proj2 |
            | proj3 |
        When I query GET "/projects/<proj>"
        Then the response code is 200
        And the response is a project with name="<proj>"

        Examples:
            | proj  |
            | proj1 |
            | proj2 |
            | proj3 |
