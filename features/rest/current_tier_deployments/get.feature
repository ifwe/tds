Feature: GET current version of application on a given tier and environment
    As a user
    I want to know what is currently deployed on a given tier in a given environment
    So that I can be informed

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
        When I query GET "/applications/<select>/tiers/tier1/environments/1"
        Then the response code is 404
        And the response contains errors:
            | location  | name          | description                                   |
            | path      | name_or_id    | Application with <descript> does not exist.   |

        Examples:
            | select    | descript      |
            | noexist   | name noexist  |
            | 500       | ID 500        |

    @rest
    Scenario Outline: get for a tier that doesn't exist
        When I query GET "/applications/app1/tiers/<select>/environments/1"
        Then the response code is 404
        And the response contains errors:
            | location  | name              | description                           |
            | path      | tier_name_or_id   | Tier with <descript> does not exist.  |

        Examples:
            | select    | descript      |
            | noexist   | name noexist  |
            | 500       | ID 500        |

    @rest
    Scenario Outline: get for an environment that doesn't exist
        When I query GET "/applications/app1/tiers/tier1/environments/<select>"
        Then the response code is 404
        And the response contains errors:
            | location  | name                      | description                                   |
            | path      | environment_name_or_id    | Environment with <descript> does not exist.   |

        Examples:
            | select    | descript      |
            | noexist   | name noexist  |
            | 500       | ID 500        |

    @rest
    Scenario: get for a tier that isn't associated with the application
        When I query GET "/applications/app1/tiers/tier2/environments/1"
        Then the response code is 403
        And the response contains errors:
            | location  | name              | description                                                                           |
            | path      | tier_name_or_id   | Association of tier tier2 with the application app1 does not exist for any projects.  |


    @rest
    Scenario Outline: get for a tier that hasn't had any deployments of the application
        When I query GET "/applications/app1/tiers/tier1/environments/1?<query>"
        Then the response code is 404
        And the response contains errors:
            | location  | name                      | description                                                                                           |
            | path      | environment_name_or_id    | <descript> deployment of application app1 on tier tier1 in development environment does not exist.    |

        Examples:
            | query                     | descript              |
            |                           | Validated or complete |
            | must_be_validated=False   | Validated or complete |
            | must_be_validated=True    | Validated             |

    @rest
    Scenario Outline: get for a tier that hasn't had any complete or validated deployments of the application
        Given there are deployments:
            | id    | user  | status    |
            | 1     | foo   | complete  |
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status    | user  | app_id    | package_id    |
            | 1     | 1             | 1                 | <status>  | foo   | 2         | 1             |
        When I query GET "/applications/app1/tiers/tier1/environments/1?<query>"
        Then the response code is 404
        And the response contains errors:
            | location  | name                      | description                                                                                           |
            | path      | environment_name_or_id    | <descript> deployment of application app1 on tier tier1 in development environment does not exist.    |

        Examples:
            | status        | query                     | descript              |
            | pending       |                           | Validated or complete |
            | pending       | must_be_validated=False   | Validated or complete |
            | pending       | must_be_validated=True    | Validated             |
            | incomplete    |                           | Validated or complete |
            | incomplete    | must_be_validated=False   | Validated or complete |
            | incomplete    | must_be_validated=True    | Validated             |
            | inprogress    |                           | Validated or complete |
            | inprogress    | must_be_validated=False   | Validated or complete |
            | inprogress    | must_be_validated=True    | Validated             |
            | invalidated   |                           | Validated or complete |
            | invalidated   | must_be_validated=False   | Validated or complete |
            | invalidated   | must_be_validated=True    | Validated             |

    @rest @wip
    Scenario Outline: get the most recent tier deployment for a given tier, application, and environment
        Given there are deployments:
            | id    | user  | status    |
            | 1     | foo   | complete  |
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status    | user  | app_id    | package_id    |
            | 1     | 1             | 1                 | validated | foo   | 2         | 1             |
            | 2     | 1             | 1                 | validated | foo   | 3         | 1             |
        And I wait 2 seconds
        And there are tier deployments:
            | id    | deployment_id | environment_id    | status    | user  | app_id    | package_id    |
            | 3     | 1             | 1                 | complete  | foo   | 2         | 1             |
        When I query GET "/applications/app1/tiers/tier1/environments/1?<query>"
        Then the response code is 200
        And the response is an object with id=<id>,deployment_id=1,environment_id=1,status="<status>",user="foo",app_id=2,package_id=1

        Examples:
            | query                     | id    | status    |
            | must_be_validated=True    | 1     | validated |
            |                           | 3     | complete  |
            | must_be_validated=False   | 3     | complete  |
