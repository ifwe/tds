Feature: GET app tier(s) from the REST API
    As a developer
    I want information on app tiers
    So that I can be informed of the current state of the database

    Background:
        Given I have a cookie with user permissions

    @rest
    Scenario: no app tiers
        When I query GET "/tiers"
        Then the response code is 200
        And the response is a list of 0 items

    @rest
    Scenario Outline: get an app tier that doesn't exist
        When I query GET "/tiers/<select>"
        Then the response code is 404
        And the response contains errors:
            | location  | name          | description                           |
            | path      | name_or_id    | Tier with <descript> does not exist.  |

        Examples:
            | select    | descript      |
            | noexist   | name noexist  |
            | 500       | ID 500        |

    @rest
    Scenario: get all tiers
        Given there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        When I query GET "/tiers"
        Then the response code is 200
        And the response is a list of 2 items
        And the response list contains objects:
            | app_type  |
            | tier1     |
            | tier2     |

    @rest
    Scenario Outline: get a single tier by name
        Given there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        When I query GET "/tiers/<tier>"
        Then the response code is 200
        And the response is an object with app_type="<tier>"

        Examples:
            | tier  |
            | tier1 |
            | tier2 |

    @rest
    Scenario Outline: get a single tier by ID
        Given there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        When I query GET "/tiers/<id>"
        Then the response code is 200
        And the response is an object with id=<id>

        Examples:
            | id    |
            | 1     |
            | 2     |
            | 3     |

    @rest
    Scenario Outline: specify limit and/or last queries
        Given there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there is a deploy target with name="tier3"
        And there is a deploy target with name="tier4"
        And there is a deploy target with name="tier5"
        When I query GET "/tiers?limit=<limit>&start=<start>"
        Then the response code is 200
        And the response is a list of <num> items
        And the response list contains id range <min> to <max>

        Examples:
            | limit | start | num   | min   | max   |
            |       |       | 5     | 2     | 6     |
            |       | 2     | 5     | 2     | 6     |
            | 10    |       | 5     | 2     | 6     |
            | 4     | 1     | 4     | 2     | 5     |

    @rest @wip
    Scenario Outline: specify unknown query
        Given there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        When I query GET "/applications?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                   |
            | query     | foo   | Unsupported query: foo. Valid parameters: ('limit', 'start'). |

        Examples:
            | query             |
            | foo=bar           |
            | limit=10&foo=bar  |
            | foo=bar&start=2   |
