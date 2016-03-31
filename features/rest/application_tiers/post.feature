Feature: POST application-tier association(s) from the REST API
    As a user
    I want to associate tiers with applications
    So that I can deploy my applications to those tiers

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
    Scenario Outline: attempt to POST for a project that doesn't exist
        When I query POST "/projects/<select>/applications/<app_select>/tiers?id=2"
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
    Scenario Outline: attempt to POST for an application that doesn't exist
        When I query POST "/projects/<select>/applications/<app_select>/tiers?name=tier1"
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
    Scenario Outline: attempt to associate a tier that doesn't exist
        When I query POST "/projects/proj1/applications/app1/tiers?<query>"
        Then the response code is 400
        And the response contains errors:
            | location  | name      | description                           |
            | query     | <name>    | Tier with <descript> does not exist.  |

        Examples:
            | query         | name  | descript      |
            | name=noexist  | name  | name noexist  |
            | id=500        | id    | ID 500        |

    @rest
    Scenario: omit required param
        When I query POST "/projects/proj1/applications/app1/tiers?"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                                   |
            | query     |       | Either name or ID for the tier is required.   |

    @rest
    Scenario Outline: add a new application-tier association
        When I query POST "/projects/proj1/applications/app1/tiers?<query>"
        Then the response code is 201
        And the response is an object with project_id=1,application_id=2,tier_id=2
        And there is a project-package with project_id=1,pkg_def_id=2,app_id=2

        Examples:
            | query             |
            | id=2              |
            | name=tier1        |
            | id=2&name=tier1   |

    @rest
    Scenario Outline: add an applicatoin-tier association that already exists
        Given the tier "tier1" is associated with the application "app1" for the project "proj1"
        When I query POST "/projects/proj1/applications/app1/tiers?<query>"
        Then the response code is 200
        And the response is an object with project_id=1,application_id=2,tier_id=2
        And there is a project-package with project_id=1,pkg_def_id=2,app_id=2

        Examples:
            | query             |
            | id=2              |
            | name=tier1        |
            | id=2&name=tier1   |
