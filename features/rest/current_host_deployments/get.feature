Feature: GET most recent deployment of an application on a given host
    As a user
    I want to know what is currently deployed on a given host
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
        And there are hosts:
            | name  | app_id    | env   |
            | host1 | 2         | dev   |
            | host2 | 2         | dev   |
            | host3 | 3         | dev   |
        And there are projects:
            | name  |
            | proj1 |
        And the tier "tier1" is associated with the application "app1" for the project "proj1"

    @rest
    Scenario Outline: get for an application that doesn't exist
        When I query GET "/applications/<select>/hosts/host1"
        Then the response code is 404
        And the response contains errors:
            | location  | name          | description                                   |
            | path      | name_or_id    | Application with <descript> does not exist.   |

        Examples:
            | select    | descript      |
            | noexist   | name noexist  |
            | 500       | ID 500        |

    @rest
    Scenario Outline: get for a host that doesn't exist
        When I query GET "/applications/app1/hosts/<select>"
        Then the response code is 404
        And the response contains errors:
            | location  | name              | description                           |
            | path      | host_name_or_id   | Host with <descript> does not exist.  |

        Examples:
            | select    | descript      |
            | noexist   | name noexist  |
            | 500       | ID 500        |

    @rest
    Scenario Outline: get for a host whose tier isn't associated with the application
        When I query GET "/applications/<a_select>/hosts/<h_select>"
        Then the response code is 403
        And the response contains errors:
            | location  | name              | description                                                                                           |
            | path      | host_name_or_id   | Association of tier tier2 of host host3 with the application app1 does not exist for any projects.    |

        Examples:
            | a_select  | h_select  |
            | 2         | host3     |
            | app1      | 3         |

    @rest
    Scenario: get for a host that hasn't had any deployments of the application
        When I query GET "/applications/app1/hosts/host1"
        Then the response code is 404
        And the response contains errors:
            | location  | name              | description                                                               |
            | path      | host_name_or_id   | Completed deployment of application app1 on host host1 does not exist.    |

    @rest
    Scenario Outline: get for a host that hasn't had any complete deployments of the application
        Given there are deployments:
            | id    | user  | status    |
            | 1     | foo   | complete  |
        And there are host deployments:
            | id    | deployment_id | status    | user  | host_id   | package_id    |
            | 1     | 1             | <status>  | foo   | 1         | 1             |
        When I query GET "/applications/app1/hosts/host1"
        Then the response code is 404
        And the response contains errors:
            | location  | name              | description                                                               |
            | path      | host_name_or_id   | Completed deployment of application app1 on host host1 does not exist.    |

        Examples:
            | status        |
            | pending       |
            | inprogress    |
            | failed        |

    @rest
    Scenario Outline: get the most recent host deployment for a given host
        Given there are deployments:
            | id    | user  | status    |
            | 1     | foo   | complete  |
        And there are host deployments:
            | id    | deployment_id | status    | user  | host_id   | package_id    |
            | 1     | 1             | ok        | foo   | 1         | 1             |
        And I wait 1 seconds
        And there are host deployments:
            | id    | deployment_id | status    | user  | host_id   | package_id    |
            | 2     | 1             | <status>  | foo   | 1         | 2             |
        When I query GET "/applications/app1/hosts/host1"
        Then the response code is 200
        And the response is an object with id=<id>,deployment_id=1,status="ok",host_id=1,package_id=<pkg_id>

        Examples:
            | status        | id    | pkg_id    |
            | pending       | 1     | 1         |
            | inprogress    | 1     | 1         |
            | failed        | 1     | 1         |
            | ok            | 2     | 2         |

    @rest
    Scenario: specify select query
        Given there are deployments:
            | id    | user  | status    |
            | 1     | foo   | complete  |
        And there are host deployments:
            | id    | deployment_id | status    | user  | host_id   | package_id    |
            | 1     | 1             | ok        | foo   | 1         | 1             |
        And I wait 1 seconds
        And there are host deployments:
            | id    | deployment_id | status    | user  | host_id   | package_id    |
            | 2     | 1             | pending   | foo   | 1         | 2             |
        When I query GET "/applications/app1/hosts/host1?select=id,deployment_id"
        Then the response code is 200
        And the response is an object with id=1,deployment_id=1
        And the response object does not contain attributes status,host_id,package_id
