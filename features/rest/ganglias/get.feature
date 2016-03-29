Feature: GET Ganglia(s) from the REST API
    As an admin
    I want information on Ganglia objects
    So that I can be informed of the current state of the database

    Background:
        Given I have a cookie with user permissions
        And there is a Ganglia with cluster_name="ganglia1"
        And there is a Ganglia with cluster_name="ganglia2"

    @rest
    Scenario Outline: get a Ganglia that doesn't exist
        When I query GET "/ganglias/<select>"
        Then the response code is 404
        And the response contains errors:
            | location  | name          | description                               |
            | path      | name_or_id    | Ganglia with <descript> does not exist.   |

        Examples:
            | select    | descript      |
            | noexist   | name noexist  |
            | 500       | ID 500        |

    @rest
    Scenario: get all Ganglias
        When I query GET "/ganglias"
        Then the response code is 200
        And the response is a list of 3 items
        And the response list contains objects:
            | name      |
            | ganglia1  |
            | ganglia2  |

    @rest
    Scenario: get all Ganglias with select query
        When I query GET "/ganglias?select=name"
        Then the response code is 200
        And the response is a list of 3 items
        And the response list contains objects:
            | name      |
            | ganglia1  |
            | ganglia2  |
        And the response list objects do not contain attributes id,port

    @rest
    Scenario Outline: get a single Ganglia
        When I query GET "/ganglias/<select>"
        Then the response code is 200
        And the response is an object with name="ganglia1"

        Examples:
            | select    |
            | ganglia1  |
            | 2         |

    @rest
    Scenario Outline: get a single Ganglia with select query
        When I query GET "/ganglias/<select>?select=name"
        Then the response code is 200
        And the response is an object with name="ganglia1"
        And the response object does not contain attributes id,port

        Examples:
            | select    |
            | ganglia1  |
            | 2         |

    @rest
    Scenario Outline: specify limit and/or last queries
        Given there is a Ganglia with cluster_name="ganglia3"
        And there is a Ganglia with cluster_name="ganglia4"
        When I query GET "/ganglias?limit=<limit>&start=<start>"
        Then the response code is 200
        And the response is a list of <num> items
        And the response list contains id range <min> to <max>

        Examples:
            | limit | start | num   | min   | max   |
            |       |       | 5     | 1     | 5     |
            |       | 2     | 4     | 2     | 5     |
            | 10    |       | 5     | 1     | 5     |
            | 4     | 1     | 4     | 1     | 4     |

    @rest
    Scenario Outline: specify unknown query
        When I query GET "/ganglias?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                               |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['limit', 'select', 'start'].   |

        Examples:
            | query             |
            | foo=bar           |
            | limit=10&foo=bar  |
            | foo=bar&start=2   |
