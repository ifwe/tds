Feature: REST API bystander HEAD
    As a developer
    I want to test my GET query
    So that I can be sure my query is not malformed

    Background:
        Given I have a cookie with user permissions

    @rest
    Scenario: get with empty database
        When I query HEAD "/bystander"
        Then the response code is 200

    @rest
    Scenario: pass a parameter
        When I query HEAD "/bystander?foo=bar"
        Then the response code is 422
        And the response body is empty

    @rest
    Scenario: get bystander info
        Given there is a project with name="proj1"
        And there is a project with name="proj2"
        And there is a project with name="proj3"

        And there is an application with pkg_name="app1"
        And there are packages:
            | version   | revision  | status    |
            | 1         | 1         | completed |
            | 2         | 2         | completed |
            | 3         | 3         | completed |

        And there is an application with pkg_name="app2"
        And there are packages:
            | version   | revision  | status    |
            | 1         | 4         | completed |
            | 2         | 5         | completed |
            | 3         | 6         | completed |

        And there is an application with pkg_name="app3"
        And there are packages:
            | version   | revision  | status    |
            | 1         | 7         | completed |
            | 2         | 8         | failed    |
            | 3         | 9         | removed   |

        And there is an environment with name="dev"
        And there is an environment with name="stage"
        And there is an environment with name="prod"

        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there is a deploy target with name="tier3"

        And the tier "tier1" is associated with the application "app1" for the project "proj1"
        And the tier "tier2" is associated with the application "app2" for the project "proj2"
        And the tier "tier3" is associated with the application "app3" for the project "proj3"

        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | complete  |
            | 2     | bar   | canceled  |
            | 3     | baz   | failed    |

        And there are tier deployments:
            | id    | deployment_id | environment_id    | status    | user  | app_id    | package_id    |
            | 1     | 1             | 1                 | complete  | foo   | 2         | 1             |
            | 2     | 1             | 1                 | complete  | foo   | 3         | 4             |
            | 3     | 1             | 1                 | complete  | foo   | 4         | 9             |
            | 4     | 2             | 2                 | complete  | foo   | 2         | 2             |
            | 5     | 2             | 2                 | complete  | foo   | 3         | 6             |
            | 6     | 2             | 2                 | complete  | foo   | 4         | 8             |
            | 7     | 3             | 3                 | complete  | foo   | 2         | 3             |
            | 8     | 3             | 3                 | complete  | foo   | 3         | 5             |
            | 9     | 3             | 3                 | complete  | foo   | 4         | 7             |

        When I query HEAD "/bystander"
        Then the response code is 200
        And the response body is empty
