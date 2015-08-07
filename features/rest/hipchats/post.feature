Feature: POST HipChat(s) from the REST API
    As an admin
    I want to add a new HipChat object
    So that it can be used in the database

    Background:
        Given I have a cookie with admin permissions
        And there is a HipChat with room_name="hipchat1"
        And there is a HipChat with room_name="hipchat2"

    @rest
    Scenario Outline: add a new Ganglia
        When I query POST "/hipchats?name=hipchat3&<query>"
        Then the response code is 201
        And the response is an object with name="hipchat3"<props>
        And there is a HipChat with room_name="hipchat3"<props>

        Examples:
            | query | props     |
            |       |           |
            | id=20 | ,id=20    |

    @rest
    Scenario: omit required field
        When I query POST "/hipchats?id=20"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description               |
            | query     |       | name is a required field. |
        And there is no HipChat with id=20

    @rest
    Scenario Outline: pass an invalid parameter
        When I query POST "/hipchats?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                               |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['id', 'name']. |
        And there is no HipChat with room_name="hipchat3"
        And there is no HipChat with id=3

        Examples:
            | query                 |
            | name=hipchat3&foo=bar |
            | foo=bar&name=hipchat3 |
