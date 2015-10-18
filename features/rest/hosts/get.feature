Feature: GET host(s) from the REST API
    As a developer
    I want information on hosts
    So that I can be informed of the current state of the database

    Background:
        Given I have a cookie with user permissions
        And there is an environment with name="dev"

    @rest
    Scenario: no hosts
        When I query GET "/hosts"
        Then the response code is 200
        And the response is a list of 0 items

    @rest
    Scenario Outline: get a host that doesn't exist
        When I query GET "/hosts/<select>"
        Then the response code is 404
        And the response contains errors:
            | location  | name          | description                           |
            | path      | name_or_id    | Host with <descript> does not exist.  |

        Examples:
            | select    | descript      |
            | noexist   | name noexist  |
            | 500       | ID 500        |

    @rest
    Scenario: get all hosts
        Given there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
        When I query GET "/hosts"
        Then the response code is 200
        And the response is a list of 2 items
        And the response list contains objects:
            | name  |
            | host1 |
            | host2 |

    @rest
    Scenario Outline: get a single host by name
        Given there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
        When I query GET "/hosts/<host>"
        Then the response code is 200
        And the response is an object with name="<host>"

        Examples:
            | host  |
            | host1 |
            | host2 |

    @rest
    Scenario Outline: get a single host by ID
        Given there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
        When I query GET "/hosts/<id>"
        Then the response code is 200
        And the response is an object with id=<id>

        Examples:
            | id    |
            | 1     |
            | 2     |

    @rest
    Scenario Outline: specify limit and/or last queries
        Given there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
            | host3 | dev   |
            | host4 | dev   |
            | host5 | dev   |
            | host6 | dev   |
        When I query GET "/hosts?limit=<limit>&start=<start>"
        Then the response code is 200
        And the response is a list of <num> items
        And the response list contains id range <min> to <max>

        Examples:
            | limit | start | num   | min   | max   |
            |       |       | 6     | 1     | 6     |
            |       | 2     | 5     | 2     | 6     |
            | 10    |       | 6     | 1     | 6     |
            | 4     | 1     | 4     | 1     | 4     |

    @rest
    Scenario Outline: specify unknown query
        Given there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
        When I query GET "/hosts?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                   |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['limit', 'start']. |

        Examples:
            | query             |
            | foo=bar           |
            | limit=10&foo=bar  |
            | foo=bar&start=2   |
