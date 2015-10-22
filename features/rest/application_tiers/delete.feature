Feature: DELETE application-tier association(s) from the REST API
    As a user
    I want to disassociate tiers from applications
    So that it is no longer possible to deploy those applications to those tiers

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
        When I query DELETE "/projects/<select>/applications/<app_select>/tiers/2"
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
    Scenario Outline: attempt to DELETE for an application that doesn't exist
        When I query DELETE "/projects/<select>/applications/<app_select>/tiers/2"
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
    Scenario Outline: attempt to DELETE for a tier that doesn't exist
        When I query DELETE "/projects/proj1/applications/app1/tiers/<select>"
        Then the response code is 404
        And the response contains errors:
            | location  | name              | description                           |
            | path      | tier_name_or_id   | Tier with <descript> does not exist.  |

        Examples:
            | select    | descript      |
            | noexist   | name noexist  |
            | 500       | ID 500        |

    @rest
    Scenario Outline: attempt to DELETE an application-tier association that doesn't exist
        When I query DELETE "/projects/proj1/applications/app1/tiers/<select>"
        Then the response code is 404
        And the response contains errors:
            | location  | name              | description                                                                               |
            | path      | tier_name_or_id   | Association of tier tier1 with the application app1 for the project proj1 does not exist. |

        Examples:
            | select    |
            | 2         |
            | tier1     |

    @rest
    Scenario Outline: delete an application-tier association
        Given the tier "tier1" is associated with the application "app1" for the project "proj1"
        When I query DELETE "/projects/proj1/applications/app1/tiers/<select>"
        Then the response code is 200
        And the response is an object with project_id=1,application_id=2,tier_id=2
        And there is no project-package with project_id=1,pkg_def_id=2,app_id=2

        Examples:
            | select    |
            | 2         |
            | tier1     |
