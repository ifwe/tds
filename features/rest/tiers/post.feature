Feature: POST app tier(s) from the REST API
    As an admin
    I want to add a new app tier
    So that developers can deploy to it using TDS

    Background:
        #TODO: Change to admin permissions
        Given I have a cookie with user permissions
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"

    @rest
    Scenario Outline: add a new tier
        When I query POST "/tiers?name=tier3&<params>"
        Then the response code is 201
        And the response is an object with name="tier3"<props>

        Examples:
            | params                    | props                         |
            |                           |                               |
            | status=inactive           | ,status="inactive"            |
            | puppet_class=cls          | ,puppet_class="cls"           |
            | distribution=centos7.1    | ,distribution="centos7.1"     |

    @rest
    Scenario Outline: omit required fields
        When I query POST "/tiers?<params>"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description               |
            | query     |       | name is a required field. |
        And there is no deploy target with id=4

        Examples:
            | params                    |
            |                           |
            | status=inactive           |

    @rest
    Scenario Outline: pass an invalid parameter
        When I query POST "/tiers?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                                                                                                                   |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['status', 'puppet_class', 'hosts', 'name', 'distribution', 'ganglia_group_name', 'hipchats', 'id', 'ganglia_id'].  |
        And there is no deploy target with name="tier3"
        And there is no deploy target with id=4

        Examples:
            | query                 |
            | name=tier3&foo=bar    |
            | foo=bar&name=tier3    |

    @rest
    Scenario Outline: attempt to violate a unique constraint
        When I query POST "/tiers?<query>"
        Then the response code is 409
        And the response contains errors:
            | location  | name      | description                                                           |
            | query     | <name>    | Unique constraint violated. A tier with this <type> already exists.   |

        Examples:
            | query             | name  | type  |
            | name=tier2        | name  | name  |
            | name=tier2&id=1   | name  | name  |
            | name=tier2&id=1   | id    | ID    |
