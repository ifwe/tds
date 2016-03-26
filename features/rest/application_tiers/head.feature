Feature: HEAD application-tier association(s) from the REST API
    As a user
    I want to test my GET query
    So that I can be sure my query is not malformed

    Background:
        Given I have a cookie with user permissions
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are projects:
            | name  |
            | proj1 |
            | proj2 |
        And there are applications:
            | name  |
            | app1  |
            | app2  |

    @rest
    Scenario Outline: get all tiers for a project that doesn't exist
        When I query HEAD "/projects/<select>/applications/<app_select>/tiers"
        Then the response code is 404
        And the response body is empty

        Examples:
            | select    | app_select    |
            | noexist   | app1          |
            | noexist   | 1             |
            | noexist   | 500           |
            | noexist   | noexist       |
            | 500       | app1          |
            | 500       | 1             |
            | 500       | 500           |
            | 500       | noexist       |

    @rest
    Scenario Outline: get all tiers for an application that doesn't exist
        When I query HEAD "/projects/<select>/applications/<app_select>/tiers"
        Then the response code is 404
        And the response body is empty

        Examples:
            | select    | app_select    |
            | proj1     | noexist       |
            | 1         | noexist       |
            | 500       | noexist       |
            | noexist   | noexist       |
            | proj1     | 500           |
            | 1         | 500           |
            | 500       | 500           |
            | noexist   | 500           |

    @rest
    Scenario Outline: get an application-tier association for a tier that doesn't exist
        When I query HEAD "/projects/<select>/applications/<app_select>/tiers/<tier_select>"
        Then the response code is 404
        And the response body is empty

        Examples:
            | select    | app_select    | tier_select   |
            | proj1     | app1          | noexist       |
            | 500       | app1          | noexist       |
            | proj1     | 500           | noexist       |
            | proj1     | app1          | 500           |
            | noexist   | app1          | 500           |
            | proj1     | noexist       | 500           |

    @rest
    Scenario: get an application-tier association that doesn't exist
        When I query HEAD "/projects/proj1/applications/app1/tiers/tier1"
        Then the response code is 404
        And the response body is empty

    @rest
    Scenario: get all application-tier associations
        Given the tier "tier1" is associated with the application "app1" for the project "proj1"
        And the tier "tier2" is associated with the application "app1" for the project "proj1"
        When I query HEAD "/projects/proj1/applications/app1/tiers"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario: get a specific application-tier association
        Given the tier "tier1" is associated with the application "app1" for the project "proj1"
        And the tier "tier2" is associated with the application "app1" for the project "proj1"
        When I query HEAD "/projects/proj1/applications/app1/tiers/tier1"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario Outline: attempt to use start and/or limit queries
        Given the tier "tier1" is associated with the application "app1" for the project "proj1"
        And the tier "tier2" is associated with the application "app1" for the project "proj1"
        When I query HEAD "/projects/proj1/applications/app1/tiers?<query>"
        Then the response code is 422
        And the response body is empty

        Examples:
            | query             |
            | limit=10          |
            | limit=10&start=1  |
            | limit=10&start=1  |
            | start=1           |
