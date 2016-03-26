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
            | location  | name      | description                                                                                                                                                                           |
            | query     | status    | Unsupported query: status. Valid parameters: ['cab', 'cage', 'console_port', 'distribution', 'environment_id', 'id', 'limit', 'name', 'rack', 'select', 'start', 'state', 'tier_id']. |

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
