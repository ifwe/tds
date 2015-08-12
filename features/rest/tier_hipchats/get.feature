Feature: GET tier-hipchat relationship(s) from the REST API
    As a user
    I want to know the current HipChats associated with a tier
    So that I can be informed of the current state of the database

    Background:
        Given I have a cookie with user permissions
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are hipchat rooms:
            | room_name |
            | hipchat1  |
            | hipchat2  |
        And the deploy target "tier1" is associated with the hipchat "hipchat1"
        And the deploy target "tier1" is associated with the hipchat "hipchat2"

    @rest
    Scenario: get hipchats for a tier that doesn't exist
        When I query GET "/tiers/foo/hipchats"
        Then the response code is 404
        And the response contains errors:
            | location  | name          | description                           |
            | path      | name_or_id    | Tier with name foo does not exist.    |

    @rest
    Scenario: get all hipchats associated with a tier
        When I query GET "/tiers/tier1/hipchats"
        Then the response code is 200
        And the response is a list of 2 items
        And the response list contains objects:
            | name      |
            | hipchat1  |
            | hipchat2  |

    # @rest @wip
    # Scenario Outline: get a specific hipchat
    #     When I query GET "/tiers/tier1/hipchats/<select>"
    #     Then the response code is 200
    #     And the response is an object with name="hipchat1",id=1
    #
    #     Examples:
    #         | select    |
    #         | hipchat1  |
    #         | 1         |
    #
    # @rest @wip
    # Scenario: pass a parameter
    #     When I query GET "/tiers/tier1/hipchats?limit=10&start=10"
    #     Then the response code is 401
    #     And the response contains errors:
    #         | location  | name  | description                               |
    #         | query     | limit | Unsupported query: start.                 |
    #         | query     | start | Unsupported query: start.                 |
