Feature: GET deployment(s) from the REST API
    As a developer
    I want information on deployments
    So that I can be informed of the current state of the database

    Background:
        Given I have a cookie with user permissions

    @rest
    Scenario: no deployments
        When I query GET "/deployments"
        Then the response code is 200
        And the response is a list of 0 items

    @rest
    Scenario: get a deployment that doesn't exist
        When I query GET "/deployments/500"
        Then the response code is 404
        And the response contains errors:
            | location  | name  | description                               |
            | path      | id    | Deployment with ID 500 does not exist.    |
