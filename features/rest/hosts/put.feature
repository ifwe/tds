Feature: PUT host(s) from the REST API
    As an admin
    I want to update a host
    So that database information reflects the current environment state

    Background:
        Given I have a cookie with admin permissions
        And there is an environment with name="dev"
        And there is a deploy target with name="tier1"
        And there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
        And the hosts are associated with the deploy target
        And there is an environment with name="stage"
        And there is a deploy target with name="tier2"

    @rest
    Scenario Outline: update a host
        When I query PUT "/hosts/<select>?<params>"
        Then the response code is 200
        And the response is an object with <props>

        Examples:
            | select    | params                            | props                                                 |
            | host1     |                                   | name="host1",id=1                                     |
            | 1         |                                   | name="host1",id=1                                     |
            | host1     | rack=100&cage=20&environment_id=2 | name="host1",id=1,rack=100,cage=20,environment_id=2   |
            | 1         | rack=100&cage=20&environment_id=2 | name="host1",id=1,rack=100,cage=20,environment_id=2   |
            | host1     | tier_id=2&kernel_version=foo      | name="host1",id=1,tier_id=2,kernel_version="foo"      |
            | 1         | tier_id=2&kernel_version=foo      | name="host1",id=1,tier_id=2,kernel_version="foo"      |
            | host1     | name=host3                        | name="host3",id=1                                     |
            | 1         | name=host3                        | name="host3",id=1                                     |

    @rest
    Scenario Outline: attempt to update a host that doesn't exist
        When I query PUT "/hosts/<select>?name=host100"
        Then the response code is 404
        And the response contains errors:
            | location  | name          | description                           |
            | path      | name_or_id    | Host with <descript> does not exist.  |
        And there is no host with name="host100"

        Examples:
            | select    | descript      |
            | noexist   | name noexist  |
            | 500       | ID 500        |

    @rest
    Scenario Outline: pass an invalid parameter
        When I query PUT "/hosts/<select>?name=host100&foo=bar"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                                                                                                                                                                           |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['power_circuit', 'environment_id', 'console_port', 'timezone', 'cage', 'name', 'kernel_version', 'arch', 'state', 'power_port', 'cab', 'distribution', 'tier_id', 'rack']. |

        Examples:
            | select    |
            | host1     |
            | 1         |
