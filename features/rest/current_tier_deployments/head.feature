Feature: HEAD most recent deployment of an application on a given tier and environment
    As a user
    I want to test my GET query
    So that I can be sure my query is not malformed

    Background:
        Given I have a cookie with user permissions
        And there is an environment with name="dev"
        And there is an application with name="app1"
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
            | 1         | 2         |
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are projects:
            | name  |
            | proj1 |
        And the tier "tier1" is associated with the application "app1" for the project "proj1"

    @rest
    Scenario Outline: get for an application that doesn't exist
        When I query HEAD "/applications/<select>/tiers/tier1/environments/1"
        Then the response code is 404
        And the response body is empty

        Examples:
            | select    |
            | noexist   |
            | 500       |

    @rest
    Scenario Outline: get for a tier that doesn't exist
        When I query HEAD "/applications/app1/tiers/<select>/environments/1"
        Then the response code is 404
        And the response body is empty

        Examples:
            | select    |
            | noexist   |
            | 500       |

    @rest
    Scenario Outline: get for an environment that doesn't exist
        When I query HEAD "/applications/app1/tiers/tier1/environments/<select>"
        Then the response code is 404
        And the response body is empty

        Examples:
            | select    |
            | noexist   |
            | 500       |

    @rest
    Scenario Outline: get for a tier that isn't associated with the application
        When I query HEAD "/applications/<a_select>/tiers/<t_select>/environments/<e_select>"
        Then the response code is 403
        And the response body is empty

        Examples:
            | a_select  | t_select  | e_select      |
            | 2         | tier2     | 1             |
            | app1      | 3         | 1             |
            | app1      | tier2     | development   |

    @rest
    Scenario Outline: get for a tier that hasn't had any deployments of the application
        Given there is an environment with name="stage"
        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | complete  |
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status    | user  | app_id    | package_id    |
            | 1     | 1             | 2                 | complete  | foo   | 2         | 1             |
        When I query HEAD "/applications/app1/tiers/tier1/environments/1?<query>"
        Then the response code is 404
        And the response body is empty

        Examples:
            | query                     |
            |                           |
            | must_be_validated=False   |
            | must_be_validated=True    |

    @rest
    Scenario Outline: get for a tier that hasn't had any complete or validated deployments of the application
        Given there are deployments:
            | id    | user  | status    |
            | 1     | foo   | complete  |
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status    | user  | app_id    | package_id    |
            | 1     | 1             | 1                 | <status>  | foo   | 2         | 1             |
        When I query HEAD "/applications/app1/tiers/tier1/environments/1?<query>"
        Then the response code is 404
        And the response body is empty

        Examples:
            | status        | query                     |
            | pending       |                           |
            | pending       | must_be_validated=False   |
            | pending       | must_be_validated=True    |
            | incomplete    |                           |
            | incomplete    | must_be_validated=False   |
            | incomplete    | must_be_validated=True    |
            | inprogress    |                           |
            | inprogress    | must_be_validated=False   |
            | inprogress    | must_be_validated=True    |
            | invalidated   |                           |
            | invalidated   | must_be_validated=False   |
            | invalidated   | must_be_validated=True    |

    @rest
    Scenario Outline: get the most recent tier deployment for a given tier, application, and environment
        Given there are deployments:
            | id    | user  | status    |
            | 1     | foo   | complete  |
            | 2     | foo   | complete  |
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status    | user  | app_id    | package_id    |
            | 1     | 1             | 1                 | validated | foo   | 2         | 2             |
            | 2     | 1             | 1                 | validated | foo   | 3         | 1             |
        And I wait 1 seconds
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status    | user  | app_id    | package_id    |
            | 3     | 1             | 1                 | complete  | foo   | 2         | 2             |
        And I wait 1 seconds
        And there is an environment with name="stage"
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status    | user  | app_id    | package_id    |
            | 4     | 2             | 2                 | validated | foo   | 2         | 1             |
        When I query HEAD "/applications/app1/tiers/tier1/environments/1?<query>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | query                     |
            | must_be_validated=True    |
            |                           |
            | must_be_validated=False   |

    @rest
    Scenario Outline: specify select query
        Given there are deployments:
            | id    | user  | status    |
            | 1     | foo   | complete  |
            | 2     | foo   | complete  |
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status    | user  | app_id    | package_id    |
            | 1     | 1             | 1                 | validated | foo   | 2         | 2             |
            | 2     | 1             | 1                 | validated | foo   | 3         | 1             |
        And I wait 1 seconds
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status    | user  | app_id    | package_id    |
            | 3     | 1             | 1                 | complete  | foo   | 2         | 2             |
        And I wait 1 seconds
        And there is an environment with name="stage"
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status    | user  | app_id    | package_id    |
            | 4     | 2             | 2                 | validated | foo   | 2         | 1             |
        When I query HEAD "/applications/app1/tiers/tier1/environments/1?select=id,deployment_id,status&<query>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | query                     |
            | must_be_validated=True    |
            |                           |
            | must_be_validated=False   |
