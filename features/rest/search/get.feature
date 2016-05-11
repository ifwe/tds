Feature: REST API search GET
    As a developer
    I want to find objects matching my specifications
    So that I can use that information to more easily interact with the API

    Background:
        Given I have a cookie with user permissions

    @rest
    Scenario: get an unknown object type
        When I query GET "/search/foo?"
        Then the response code is 404
        And the response contains errors:
            | location  | name      | description                                                                                                                                                                                                                           |
            | path      | obj_type  | Unknown object type foo. Supported object types are: ['application_tiers', 'applications', 'deployments', 'environments', 'ganglias', 'hipchats', 'host_deployments', 'hosts', 'packages', 'projects', 'tier_deployments', 'tiers'].  |

    @rest
    Scenario: get all projects
        Given there are projects:
            | name  |
            | proj1 |
            | proj2 |
            | proj3 |
        When I query GET "/search/projects?"
        Then the response code is 200
        And the response is a list of 3 items
        And the response list contains objects:
            | name  |
            | proj1 |
            | proj2 |
            | proj3 |

    @rest
    Scenario: specify select query
        Given there are projects:
            | name  |
            | proj1 |
            | proj2 |
            | proj3 |
        When I query GET "/search/projects?select=name"
        Then the response code is 200
        And the response is a list of 3 items
        And the response list contains objects:
            | name  |
            | proj1 |
            | proj2 |
            | proj3 |
        And the response list objects do not contain attributes id

    @rest
    Scenario: get a specific project
        Given there are projects:
            | name  |
            | proj1 |
            | proj2 |
            | proj3 |
        When I query GET "/search/projects?name=proj1"
        Then the response code is 200
        And the response is a list of 1 items
        And the response list contains objects:
            | name  |
            | proj1 |

    @rest
    Scenario: get a list of matching hosts by a param of choice type whose choices are retrieved from the DB schema
        Given there is a deploy target with name="tier1"
        And there is an environment with name="dev"
        And there are hosts:
            | name  | distribution  | env   | state     |
            | host1 | centos5.4     | dev   | repair    |
            | host2 | centos6.5     | dev   | repair    |
            | host3 | centos7.1     | dev   | repair    |
            | host4 | centos5.4     | dev   | repair    |
            | host5 | centos6.5     | dev   | escrow    |
            | host6 | centos7.1     | dev   | escrow    |
        When I query GET "/search/hosts?state=escrow"
        Then the response code is 200
        And the response is a list of 2 items
        And the response list contains objects:
            | name  | state     |
            | host5 | escrow    |
            | host6 | escrow    |

    @rest
    Scenario: pass multiple specifications
        Given there is a deploy target with name="tier1"
        And there is an environment with name="dev"
        And there are hosts:
            | name  | distribution  | env   | state     |
            | host1 | centos5.4     | dev   | repair    |
            | host2 | centos6.5     | dev   | repair    |
            | host3 | centos7.1     | dev   | repair    |
            | host4 | centos5.4     | dev   | repair    |
            | host5 | centos6.5     | dev   | escrow    |
            | host6 | centos7.1     | dev   | escrow    |
            | host7 | centos5.4     | dev   | escrow    |
            | host8 | centos5.4     | dev   | escrow    |
        When I query GET "/search/hosts?state=escrow&distribution=centos5.4"
        Then the response code is 200
        And the response is a list of 2 items
        And the response list contains objects:
            | name  | state     | distribution  |
            | host7 | escrow    | centos5.4     |
            | host8 | escrow    | centos5.4     |

    @rest
    Scenario Outline: pass non-integer limit/start queries
        Given there are projects:
            | name  |
            | proj1 |
            | proj2 |
            | proj3 |
            | proj4 |
            | proj5 |
            | proj6 |
            | proj7 |
            | proj8 |
            | proj9 |
            | proj0 |
        When I query GET "/search/projects?limit=<limit>&start=<start>"
        Then the response code is 400
        And the response contains errors:
            | location  | name      | description                                                           |
            | query     | <param>   | Validation failed: Value 2.3 for argument <param> is not an integer.  |

        Examples:
            | limit | start | param |
            | 2     | 2.3   | start |
            | 2.3   | 2     | limit |
            | 2.3   | 2.3   | limit |
            | 2.3   | 2.3   | start |

    @rest
    Scenario: pass invalid choice for choice param
        Given there is a deploy target with name="tier1"
        And there is an environment with name="dev"
        And there are hosts:
            | name  | distribution  | env   | state     |
            | host1 | centos5.4     | dev   | repair    |
            | host2 | centos6.5     | dev   | repair    |
            | host3 | centos7.1     | dev   | repair    |
            | host4 | centos5.4     | dev   | escrow    |
            | host5 | centos6.5     | dev   | escrow    |
            | host6 | centos7.1     | dev   | escrow    |
        When I query GET "/search/hosts?state=foo"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                                                                                                                               |
            | query     | state | Validation failed: Value foo for argument state must be one of: ['baremetal', 'escrow', 'operational', 'parts', 'repair', 'reserved'].    |

    @rest
    Scenario: pass unknown param in query
        Given there is a deploy target with name="tier1"
        And there is an environment with name="dev"
        And there are hosts:
            | name  | distribution  | env   |
            | host1 | centos5.4     | dev   |
            | host2 | centos6.5     | dev   |
            | host3 | centos7.1     | dev   |
            | host4 | centos5.4     | dev   |
            | host5 | centos6.5     | dev   |
            | host6 | centos7.1     | dev   |
        When I query GET "/search/hosts?status=operational"
        Then the response code is 422
        And the response contains errors:
            | location  | name      | description                                                                                                                                                                                               |
            | query     | status    | Unsupported query: status. Valid parameters: ['cab', 'cage', 'console_port', 'dc_id', 'distribution', 'environment_id', 'id', 'limit', 'name', 'rack', 'select', 'spec_id', 'start', 'state', 'tier_id']. |

    @rest
    Scenario: pass a param that is routed to the ORM name
        Given there is a deploy target with name="tier1"
        And there is an environment with name="dev"
        And there are hosts:
            | name  | distribution  | env   |
            | host1 | centos5.4     | dev   |
            | host2 | centos6.5     | dev   |
            | host3 | centos7.1     | dev   |
            | host4 | centos5.4     | dev   |
            | host5 | centos6.5     | dev   |
            | host6 | centos7.1     | dev   |
        When I query GET "/search/hosts?name=host1"
        Then the response code is 200
        And the response is a list of 1 items
        And the response list contains objects:
            | host1 | centos5.4      | dev   |

    @rest
    Scenario Outline: expect a redirect
        Given there is a deploy target with name="tier1"
        And there is an environment with name="dev"
        And there are hosts:
            | name  | distribution  | env   |
            | host1 | centos5.4     | dev   |
            | host2 | centos6.5     | dev   |
            | host3 | centos7.1     | dev   |
            | host4 | centos5.4     | dev   |
            | host5 | centos6.5     | dev   |
            | host6 | centos7.1     | dev   |
        And I have set the request headers Expect="<expectation>"
        And I have disabled redirect following
        When I query GET "/search/hosts?name=host1"
        Then the response code is <code>
        And the response header contains a location with "/hosts/1"

        Examples:
            | expectation   | code  |
            | 302 Found     | 302   |
            | 303 See Other | 303   |

    @rest
    Scenario Outline: expect a redirect with multiple results
        Given there is a deploy target with name="tier1"
        And there is an environment with name="dev"
        And there are hosts:
            | name  | distribution  | env   |
            | host1 | centos5.4     | dev   |
            | host2 | centos6.5     | dev   |
            | host3 | centos7.1     | dev   |
            | host4 | centos5.4     | dev   |
            | host5 | centos6.5     | dev   |
            | host6 | centos7.1     | dev   |
        And I have set the request headers Expect="<expectation>"
        And I have disabled redirect following
        When I query GET "/search/hosts?distribution=centos5.4"
        Then the response code is 417

        Examples:
            | expectation   |
            | 302 Found     |
            | 303 See Other |

    @rest
    Scenario: get package with user select
        Given there are applications:
            | name  |
            | app1  |
        And there are packages:
            | version   | revision  | creator   |
            | 1         | 2         | foo       |
            | 2         | 1         | foo       |
        When I query GET "/search/packages?user=foo"
        Then the response code is 200
        And the response is a list of 2 items
        And the response list contains objects:
            | user  | version   |
            | foo   | 1         |
            | foo   | 2         |

    @rest
    Scenario Outline: specify limit and/or start queries without filter query
        Given there is a deploy target with name="tier1"
        And there is an environment with name="dev"
        And there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
            | host3 | dev   |
            | host4 | dev   |
            | host5 | dev   |
        When I query GET "/search/hosts?limit=<limit>&start=<start>"
        Then the response code is 200
        And the response is a list of <num> items
        And the response list contains id range <min> to <max>

        Examples:
            | limit | start | num   | min   | max   |
            |       |       | 5     | 1     | 5     |
            |       | 3     | 3     | 3     | 5     |
            | 2     |       | 2     | 1     | 2     |
            | 2     | 3     | 2     | 3     | 4     |

    @rest
    Scenario Outline: specify limit and/or start queries with filter query
        Given there is a deploy target with name="tier1"
        And there is an environment with name="dev"
        And there are hosts:
            | name      | distribution  | env   |
            | host1     | centos5.4     | dev   |
            | host2     | centos5.4     | dev   |
            | host3     | centos7.1     | dev   |
            | host4     | centos7.1     | dev   |
            | host5     | centos6.5     | dev   |
            | host6     | centos6.5     | dev   |
            | host7     | centos6.5     | dev   |
            | host8     | centos6.5     | dev   |
            | host9     | centos6.5     | dev   |
            | host10    | centos6.5     | dev   |
            | host11    | centos6.5     | dev   |
        When I query GET "/search/hosts?distribution=centos6.5&limit=<limit>&start=<start>"
        Then the response code is 200
        And the response is a list of <num> items
        And the response list contains id range <min> to <max>

        Examples:
            | limit | start | num   | min   | max   |
            |       |       | 7     | 5     | 11    |
            |       | 8     | 4     | 8     | 11    |
            | 2     |       | 2     | 5     | 6     |
            | 2     | 8     | 2     | 8     | 9     |

    @rest
    Scenario Outline: specify before and/or after queries for deployments
        Given there are deployments:
            | id    | user  | status    | declared              |
            | 1     | foo   | pending   | 2016-01-01 01:00:00   |
            | 2     | foo   | queued    | 2016-01-01 02:00:00   |
            | 3     | foo   | pending   | 2016-01-01 03:00:00   |
            | 4     | foo   | queued    | 2016-01-01 04:00:00   |
            | 5     | foo   | queued    | 2016-01-01 04:00:01   |
        When I query GET "/search/deployments?before=<before>&after=<after>"
        Then the response code is 200
        And the response is a list of <num> items

        Examples:
            | before                | after                 | num   |
            | 0                     |                       | 0     |
            |                       | 0                     | 5     |
            | 2016-01-01            |                       | 0     |
            |                       | 2015-12-31            | 5     |
            | 2016-01-01T00:00:00   |                       | 0     |
            |                       | 2016-01-01T00:59:59   | 5     |
            | 2016-01-01T02:00:00   |                       | 1     |
            |                       | 2016-01-01T01:00:00   | 4     |
            | 2016-01-01T04:00:02   | 2016-01-01T00:59:59   | 5     |
            | 2016-01-01T04:00:01   | 2016-01-01T02:59:59   | 2     |

    @rest
    Scenario Outline: pass invalid time format for before and/or after queries
        When I query GET "/search/deployments?before=<before>&after=<after>"
        Then the response code is 400
        And the response contains errors:
            | location  | name      | description                                                                                                                                                       |
            | query     | <name>    | Validation failed: Could not parse <val> for <name> as a valid timestamp. Valid timestamp formats: %Y-%m-%d, %Y-%m-%dT%H:%M:%S, and integer seconds since epoch.  |

        Examples:
            | before    | after | name      | val   |
            | asdf      |       | before    | asdf  |
            |           | asdf  | after     | asdf  |
            | fdsa      | asdf  | before    | fdsa  |
            | fdsa      | asdf  | after     | asdf  |

    @rest
    Scenario Outline: specify before and/or after queries for host deployments
        Given there are deployments:
            | id    | user  | status    | declared              |
            | 1     | foo   | pending   | 2016-01-01 01:00:00   |
        And there is an application with name="app1"
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
        And there is an environment with name="dev"
        And there are hosts:
            | name  | env   |
            | host1 | dev   |
        And there are host deployments:
            | id    | user  | status    | realized              | deployment_id | package_id    | host_id   |
            | 1     | foo   | ok        | 2016-01-01 01:00:00   | 1             | 1             | 1         |
            | 2     | foo   | ok        | 2016-01-01 02:00:00   | 1             | 1             | 1         |
            | 3     | foo   | ok        | 2016-01-01 03:00:00   | 1             | 1             | 1         |
            | 4     | foo   | ok        | 2016-01-01 04:00:00   | 1             | 1             | 1         |
            | 5     | foo   | ok        | 2016-01-01 04:00:01   | 1             | 1             | 1         |
        When I query GET "/search/host_deployments?before=<before>&after=<after>"
        Then the response code is 200
        And the response is a list of <num> items

        Examples:
            | before                | after                 | num   |
            | 0                     |                       | 0     |
            |                       | 0                     | 5     |
            | 2016-01-01            |                       | 0     |
            |                       | 2015-12-31            | 5     |
            | 2016-01-01T00:00:00   |                       | 0     |
            |                       | 2016-01-01T00:59:59   | 5     |
            | 2016-01-01T02:00:00   |                       | 1     |
            |                       | 2016-01-01T01:00:00   | 4     |
            | 2016-01-01T04:00:02   | 2016-01-01T00:59:59   | 5     |
            | 2016-01-01T04:00:01   | 2016-01-01T02:59:59   | 2     |

    @rest
    Scenario Outline: specify before and/or after queries for tier deployments
        Given there are deployments:
            | id    | user  | status    | declared              |
            | 1     | foo   | pending   | 2016-01-01 01:00:00   |
        And there is an application with name="app1"
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
        And there is an environment with name="dev"
        And there is a deploy target with name="app1"
        And there are tier deployments:
            | id    | user  | status    | realized              | deployment_id | package_id    | app_id    | environment_id    |
            | 1     | foo   | complete  | 2016-01-01 01:00:00   | 1             | 1             | 1         | 1                 |
            | 2     | foo   | complete  | 2016-01-01 02:00:00   | 1             | 1             | 1         | 1                 |
            | 3     | foo   | complete  | 2016-01-01 03:00:00   | 1             | 1             | 1         | 1                 |
            | 4     | foo   | complete  | 2016-01-01 04:00:00   | 1             | 1             | 1         | 1                 |
            | 5     | foo   | complete  | 2016-01-01 04:00:01   | 1             | 1             | 1         | 1                 |
        When I query GET "/search/tier_deployments?before=<before>&after=<after>"
        Then the response code is 200
        And the response is a list of <num> items

        Examples:
            | before                | after                 | num   |
            | 0                     |                       | 0     |
            |                       | 0                     | 5     |
            | 2016-01-01            |                       | 0     |
            |                       | 2015-12-31            | 5     |
            | 2016-01-01T00:00:00   |                       | 0     |
            |                       | 2016-01-01T00:59:59   | 5     |
            | 2016-01-01T02:00:00   |                       | 1     |
            |                       | 2016-01-01T01:00:00   | 4     |
            | 2016-01-01T04:00:02   | 2016-01-01T00:59:59   | 5     |
            | 2016-01-01T04:00:01   | 2016-01-01T02:59:59   | 2     |

    @rest
    Scenario Outline: specify before and/or after queries for applications
        Given there are applications:
            | name  | created               |
            | app1  | 2016-01-01 01:00:00   |
            | app2  | 2016-01-01 02:00:00   |
            | app3  | 2016-01-01 03:00:00   |
            | app4  | 2016-01-01 04:00:00   |
            | app5  | 2016-01-01 04:00:01   |
        When I query GET "/search/applications?before=<before>&after=<after>"
        Then the response code is 200
        And the response is a list of <num> items

        # Numbers are b0rked because of __dummy__ app
        Examples:
            | before                | after                 | num   |
            | 0                     |                       | 0     |
            |                       | 0                     | 6     |
            | 2016-01-01            |                       | 0     |
            |                       | 2015-12-31            | 6     |
            | 2016-01-01T00:00:00   |                       | 0     |
            |                       | 2016-01-01T00:59:59   | 6     |
            | 2016-01-01T02:00:00   |                       | 1     |
            |                       | 2016-01-01T01:00:00   | 5     |
            | 2016-01-01T04:00:02   | 2016-01-01T00:59:59   | 5     |
            | 2016-01-01T04:00:01   | 2016-01-01T02:59:59   | 2     |

    @rest
    Scenario Outline: specify before and/or after queries for packages
        Given there is an application with name="app1"
        And there are packages:
            | version   | revision  | created               |
            | 1         | 1         | 2016-01-01 01:00:00   |
            | 2         | 2         | 2016-01-01 02:00:00   |
            | 3         | 3         | 2016-01-01 03:00:00   |
            | 4         | 4         | 2016-01-01 04:00:00   |
            | 5         | 5         | 2016-01-01 04:00:01   |
        When I query GET "/search/packages?before=<before>&after=<after>"
        Then the response code is 200
        And the response is a list of <num> items

        Examples:
            | before                | after                 | num   |
            | 0                     |                       | 0     |
            |                       | 0                     | 5     |
            | 2016-01-01            |                       | 0     |
            |                       | 2015-12-31            | 5     |
            | 2016-01-01T00:00:00   |                       | 0     |
            |                       | 2016-01-01T00:59:59   | 5     |
            | 2016-01-01T02:00:00   |                       | 1     |
            |                       | 2016-01-01T01:00:00   | 4     |
            | 2016-01-01T04:00:02   | 2016-01-01T00:59:59   | 5     |
            | 2016-01-01T04:00:01   | 2016-01-01T02:59:59   | 2     |
