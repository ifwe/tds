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
            | location  | name      | description                                                                                                                                                                                                       |
            | path      | obj_type  | Unknown object type foo. Supported object types are: ['tier_deployments', 'ganglias', 'environments', 'applications', 'packages', 'projects', 'tiers', 'hipchats', 'deployments', 'host_deployments', 'hosts'].   |

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
    Scenario: get a list of matching hosts by a param of choice type
        Given there is a deploy target with name="tier1"
        And there is an environment with name="dev"
        And there are hosts:
            | name  | arch      | env   |
            | host1 | i386      | dev   |
            | host2 | noarch    | dev   |
            | host3 | x86_64    | dev   |
            | host4 | i386      | dev   |
            | host5 | noarch    | dev   |
            | host6 | x86_64    | dev   |
        When I query GET "/search/hosts?arch=i386"
        Then the response code is 200
        And the response is a list of 2 items
        And the response list contains objects:
            | name  | arch  |
            | host1 | i386  |
            | host4 | i386  |

    @rest
    Scenario: get a list of matching hosts by a param of choice type whose choices are retrieved from the DB schema
        Given there is a deploy target with name="tier1"
        And there is an environment with name="dev"
        And there are hosts:
            | name  | arch      | env   | state     |
            | host1 | i386      | dev   | repair    |
            | host2 | noarch    | dev   | repair    |
            | host3 | x86_64    | dev   | repair    |
            | host4 | i386      | dev   | repair    |
            | host5 | noarch    | dev   | escrow    |
            | host6 | x86_64    | dev   | escrow    |
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
            | name  | arch      | env   | state     |
            | host1 | i386      | dev   | repair    |
            | host2 | noarch    | dev   | repair    |
            | host3 | x86_64    | dev   | repair    |
            | host4 | i386      | dev   | repair    |
            | host5 | noarch    | dev   | escrow    |
            | host6 | x86_64    | dev   | escrow    |
            | host7 | i386      | dev   | escrow    |
            | host8 | i386      | dev   | escrow    |
        When I query GET "/search/hosts?state=escrow&arch=i386"
        Then the response code is 200
        And the response is a list of 2 items
        And the response list contains objects:
            | name  | state     | arch  |
            | host7 | escrow    | i386  |
            | host8 | escrow    | i386  |

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
            | location  | name      | description                                                               |
            | query     | <param>   | Validation failed: Value 2.3 for argument <param> is not an integer.    |

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
            | name  | arch      | env   |
            | host1 | i386      | dev   |
            | host2 | noarch    | dev   |
            | host3 | x86_64    | dev   |
            | host4 | i386      | dev   |
            | host5 | noarch    | dev   |
            | host6 | x86_64    | dev   |
        When I query GET "/search/hosts?arch=foo"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                                                                                   |
            | query     | arch  | Validation failed: Value foo for argument arch must be one of: ('i386', 'noarch', 'x86_64').  |

    @rest
    Scenario: pass unknown param in query
        Given there is a deploy target with name="tier1"
        And there is an environment with name="dev"
        And there are hosts:
            | name  | arch      | env   |
            | host1 | i386      | dev   |
            | host2 | noarch    | dev   |
            | host3 | x86_64    | dev   |
            | host4 | i386      | dev   |
            | host5 | noarch    | dev   |
            | host6 | x86_64    | dev   |
        When I query GET "/search/hosts?status=operational"
        Then the response code is 422
        And the response contains errors:
            | location  | name      | description                                                                                                                                                                                                                                       |
            | query     | status    | Unsupported query: status. Valid parameters: ['arch', 'cab', 'cage', 'console_port', 'distribution', 'environment_id', 'id', 'kernel_version', 'limit', 'name', 'power_circuit', 'power_port', 'rack', 'start', 'state', 'tier_id', 'timezone'].  |

    @rest
    Scenario: pass a param that is routed to the ORM name
        Given there is a deploy target with name="tier1"
        And there is an environment with name="dev"
        And there are hosts:
            | name  | arch      | env   |
            | host1 | i386      | dev   |
            | host2 | noarch    | dev   |
            | host3 | x86_64    | dev   |
            | host4 | i386      | dev   |
            | host5 | noarch    | dev   |
            | host6 | x86_64    | dev   |
        When I query GET "/search/hosts?name=host1"
        Then the response code is 200
        And the response is a list of 1 items
        And the response list contains objects:
            | host1 | i386      | dev   |

    @rest
    Scenario Outline: expect a redirect
        Given there is a deploy target with name="tier1"
        And there is an environment with name="dev"
        And there are hosts:
            | name  | arch      | env   |
            | host1 | i386      | dev   |
            | host2 | noarch    | dev   |
            | host3 | x86_64    | dev   |
            | host4 | i386      | dev   |
            | host5 | noarch    | dev   |
            | host6 | x86_64    | dev   |
        And I have set the request headers Expect="<expectation>"
        And I have disabled redirect following
        When I query GET "/search/hosts?name=host1"
        Then the response code is <code>
        And the response header contains a location with "/hosts/1"

        Examples:
            | expectation   | code      |
            | 302 Found     | 302       |
            | 303 See Other | 303       |

    @rest
    Scenario Outline: expect a redirect with multiple results
        Given there is a deploy target with name="tier1"
        And there is an environment with name="dev"
        And there are hosts:
            | name  | arch      | env   |
            | host1 | i386      | dev   |
            | host2 | noarch    | dev   |
            | host3 | x86_64    | dev   |
            | host4 | i386      | dev   |
            | host5 | noarch    | dev   |
            | host6 | x86_64    | dev   |
        And I have set the request headers Expect="<expectation>"
        And I have disabled redirect following
        When I query GET "/search/hosts?arch=i386"
        Then the response code is 417

        Examples:
            | expectation   |
            | 302 Found     |
            | 303 See Other |

    @rest
    Scenario Outline: specify limit and/or start queries
        Given there is a deploy target with name="tier1"
        And there is an environment with name="dev"
        And there are hosts:
            | name      | arch      | env   |
            | host1     | i386      | dev   |
            | host2     | i386      | dev   |
            | host3     | x86_64    | dev   |
            | host4     | x86_64    | dev   |
            | host5     | noarch    | dev   |
            | host6     | noarch    | dev   |
            | host7     | noarch    | dev   |
            | host8     | noarch    | dev   |
            | host9     | noarch    | dev   |
            | host10    | noarch    | dev   |
            | host11    | noarch    | dev   |
        When I query GET "/search/hosts?arch=noarch&limit=<limit>&start=<start>"
        Then the response code is 200
        And the response is a list of <num> items
        And the response list contains id range <min> to <max>

        Examples:
            | limit | start | num   | min   | max   |
            |       |       | 7     | 5     | 11    |
            |       | 8     | 4     | 8     | 11    |
            | 2     |       | 2     | 5     | 6     |
            | 2     | 8     | 2     | 8     | 9     |
