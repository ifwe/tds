Feature: GET application-tier association(s) from the REST API
    As a user
    I want to know which tiers are associated with which applications for which projects
    So that I can act accordingly

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
        When I query GET "/projects/<select>/applications/<app_select>/tiers"
        Then the response code is 404
        And the response contains errors:
            | location  | name          | description                               |
            | path      | name_or_id    | Project with <descript> does not exist.   |

        Examples:
            | select    | app_select    | descript      |
            | noexist   | app1          | name noexist  |
            | noexist   | 1             | name noexist  |
            | noexist   | 500           | name noexist  |
            | noexist   | noexist       | name noexist  |
            | 500       | app1          | ID 500        |
            | 500       | 1             | ID 500        |
            | 500       | 500           | ID 500        |
            | 500       | noexist       | ID 500        |

    @rest
    Scenario Outline: get all tiers for an application that doesn't exist
        When I query GET "/projects/<select>/applications/<app_select>/tiers"
        Then the response code is 404
        And the response contains errors:
            | location  | name                      | description                                   |
            | path      | application_name_or_id    | Application with <descript> does not exist.   |

        Examples:
            | select    | app_select    | descript      |
            | proj1     | noexist       | name noexist  |
            | 1         | noexist       | name noexist  |
            | 500       | noexist       | name noexist  |
            | noexist   | noexist       | name noexist  |
            | proj1     | 500           | ID 500        |
            | 1         | 500           | ID 500        |
            | 500       | 500           | ID 500        |
            | noexist   | 500           | ID 500        |

    @rest
    Scenario Outline: get an application-tier association for a tier that doesn't exist
        When I query GET "/projects/<select>/applications/<app_select>/tiers/<tier_select>"
        Then the response code is 404
        And the response contains errors:
            | location  | name              | description                           |
            | path      | tier_name_or_id   | Tier with <descript> does not exist.  |

        Examples:
            | select    | app_select    | tier_select   | descript      |
            | proj1     | app1          | noexist       | name noexist  |
            | 500       | app1          | noexist       | name noexist  |
            | proj1     | 500           | noexist       | name noexist  |
            | proj1     | app1          | 500           | ID 500        |
            | noexist   | app1          | 500           | ID 500        |
            | proj1     | noexist       | 500           | ID 500        |

    @rest
    Scenario: get an application-tier association that doesn't exist
        When I query GET "/projects/proj1/applications/app1/tiers/tier1"
        Then the response code is 404
        And the response contains errors:
            | location  | name              | description                                                                               |
            | path      | tier_name_or_id   | Association of tier tier1 with the application app1 for the project proj1 does not exist. |

    @rest
    Scenario: get all application-tier associations
        Given the tier "tier1" is associated with the application "app1" for the project "proj1"
        And the tier "tier2" is associated with the application "app1" for the project "proj1"
        When I query GET "/projects/proj1/applications/app1/tiers"
        Then the response code is 200
        And the response is a list of 2 items
        And the response list contains an object with project_id=1,application_id=2,tier_id=2
        And the response list contains an object with project_id=1,application_id=2,tier_id=3

    @rest
    Scenario Outline: get all application-tier associations with select and limit queries
        Given the tier "tier1" is associated with the application "app1" for the project "proj1"
        And the tier "tier2" is associated with the application "app1" for the project "proj1"
        When I query GET "/projects/proj1/applications/app1/tiers?limit=<limit>&select=project_id,tier_id"
        Then the response code is 200
        And the response is a list of <limit> items
        And the response list contains an object with project_id=1,tier_id=2
        And the response list objects do not contain attributes application_id

        Examples:
            | limit |
            | 1     |
            | 2     |

    @rest
    Scenario: get a specific application-tier association
        Given the tier "tier1" is associated with the application "app1" for the project "proj1"
        And the tier "tier2" is associated with the application "app1" for the project "proj1"
        When I query GET "/projects/proj1/applications/app1/tiers/tier1"
        Then the response code is 200
        And the response is an object with project_id=1,application_id=2,tier_id=2

    @rest
    Scenario: get a specific application-tier association with select query
        Given the tier "tier1" is associated with the application "app1" for the project "proj1"
        And the tier "tier2" is associated with the application "app1" for the project "proj1"
        When I query GET "/projects/proj1/applications/app1/tiers/tier1?select=application_id"
        Then the response code is 200
        And the response is an object with application_id=2
        And the response object does not contain attributes project_id,tier_id

    @rest
    Scenario Outline: attempt to use start query
        Given the tier "tier1" is associated with the application "app1" for the project "proj1"
        And the tier "tier2" is associated with the application "app1" for the project "proj1"
        When I query GET "/projects/proj1/applications/app1/tiers?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name      | description                                                       |
            | query     | <name>    | Unsupported query: <name>. Valid parameters: ['limit', 'select']. |

        Examples:
            | query             | name  |
            | limit=10&start=1  | start |
            | start=1           | start |
