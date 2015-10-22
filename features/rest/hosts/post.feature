Feature: POST host(s) from the REST API
    As an admin
    I want to add a new host
    So that developers can deploy to it using TDS

    Background:
        Given I have a cookie with admin permissions
        And there is an environment with name="dev"
        And there is a deploy target with name="tier1"
        And there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
        And the hosts are associated with the deploy target

    @rest
    Scenario Outline: add a new host
        When I query POST "/hosts?name=host3&tier_id=2&<params>"
        Then the response code is 201
        And the response is an object with name="host3",tier_id=2<props>

        Examples:
            | params                            | props                                 |
            |                                   |                                       |
            | cage=1&cab=foo&rack=3             | ,cage=1,cab="foo",rack=3              |
            | kernel_version=foo                | ,kernel_version="foo"                 |
            | console_port=foo&power_port=foo   | ,console_port="foo",power_port="foo"  |

    @rest
    Scenario Outline: omit required fields
        When I query POST "/hosts?<params>"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                   |
            | query     |       | <name> is a required field.   |
        And there is no host with id=3

        Examples:
            | params        | name      |
            | name=host3    | tier_id   |
            | tier_id=2     | name      |
            | cage=1        | name      |
            | cage=1        | tier_id   |

    @rest
    Scenario Outline: pass an invalid parameter
        When I query POST "/hosts?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                                                                                                                                                                           |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['arch', 'cab', 'cage', 'console_port', 'distribution', 'environment_id', 'kernel_version', 'name', 'power_circuit', 'power_port', 'rack', 'state', 'tier_id', 'timezone']. |
        And there is no host with name="host3"
        And there is no host with id=3

        Examples:
            | query                         |
            | name=host3&tier_id=2&foo=bar  |
            | foo=bar&tier_id=2&name=host   |

    @rest
    Scenario: attempt to violate a unique constraint
        When I query POST "/hosts?tier_id=2&name=host2"
        Then the response code is 409
        And the response contains errors:
            | location  | name  | description                                                       |
            | query     | name  | Unique constraint violated. A host with this name already exists. |

    @rest
    Scenario: pass a tier ID for a tier that doesn't exist
        When I query POST "/hosts?tier_id=500&name=host3"
        Then the response code is 400
        And the response contains errors:
            | location  | name      | description                       |
            | query     | tier_id   | No app tier with ID 500 exists.   |
        And there is no host with name="host3"
        And there is no host with id=3

    @rest
    Scenario Outline: pass a non-integer for an integer param
        When I query POST "/hosts?name=host3&<query>"
        Then the response code is 400
        And the response contains errors:
            | location  | name      | description                                                               |
            | query     | <name>    | Validation failed: Value 3.1415 for argument <type> is not an integer.    |
        And there is no host with name="host3"
        And there is no host with id=<id>

        Examples:
            | query                 | name              | id        | type              |
            | tier_id=3.1415        | tier_id           | 3         | tier_id           |
            | environment_id=3.1415 | environment_id    | 3.1415    | environment_id    |