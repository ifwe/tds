Feature: REST API search HEAD
    As a developer
    I want to test my GET query
    So that I can be sure my query is not malformed

    Background:
        Given I have a cookie with user permissions

    @rest
    Scenario: get an unknown object type
        When I query HEAD "/search/foo?"
        Then the response code is 404
        And the response body is empty

    @rest
    Scenario: get all projects
        Given there are projects:
            | name  |
            | proj1 |
            | proj2 |
            | proj3 |
        When I query HEAD "/search/projects?"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario: specify select query
        Given there are projects:
            | name  |
            | proj1 |
            | proj2 |
            | proj3 |
        When I query HEAD "/search/projects?select=name"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario: get a specific project
        Given there are projects:
            | name  |
            | proj1 |
            | proj2 |
            | proj3 |
        When I query HEAD "/search/projects?name=proj1"
        Then the response code is 200
        And the response body is empty

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
        When I query HEAD "/search/hosts?state=escrow"
        Then the response code is 200
        And the response body is empty

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
        When I query HEAD "/search/hosts?state=escrow&distribution=centos5.4"
        Then the response code is 200
        And the response body is empty

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
        When I query HEAD "/search/projects?limit=<limit>&start=<start>"
        Then the response code is 400
        And the response body is empty

        Examples:
            | limit | start |
            | 2     | 2.3   |
            | 2.3   | 2     |
            | 2.3   | 2.3   |
            | 2.3   | 2.3   |

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
        When I query HEAD "/search/hosts?state=foo"
        Then the response code is 400
        And the response body is empty

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
        When I query HEAD "/search/hosts?status=operational"
        Then the response code is 422
        And the response body is empty

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
        When I query HEAD "/search/hosts?name=host1"
        Then the response code is 200
        And the response body is empty

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
        When I query HEAD "/search/hosts?name=host1"
        Then the response code is <code>
        And the response header contains a location with "/hosts/1"
        And the response body is empty

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
        When I query HEAD "/search/hosts?distribution=centos5.4"
        Then the response code is 417
        And the response body is empty

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
        When I query HEAD "/search/hosts?limit=<limit>&start=<start>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | limit | start |
            |       |       |
            |       | 3     |
            | 2     |       |
            | 2     | 3     |

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
        When I query HEAD "/search/hosts?distribution=centos6.5&limit=<limit>&start=<start>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | limit | start |
            |       |       |
            |       | 8     |
            | 2     |       |
            | 2     | 8     |
