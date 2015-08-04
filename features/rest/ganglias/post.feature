Feature: POST Ganglia(s) from the REST API
    As an admin
    I want to add a new Ganglia object
    So that it can be used in the database

    Background:
        Given I have a cookie with admin permissions
        And there is a Ganglia with cluster_name="ganglia1"
        And there is a Ganglia with cluster_name="ganglia2"

    @rest
    Scenario Outline: add a new Ganglia
        When I query POST "/ganglias?name=ganglia3&<query>"
        Then the response code is 201
        And the response is an object with name="ganglia3"<props>
        And there is a Ganglia with cluster_name="ganglia3"<props>

        Examples:
            | query             | props             |
            |                   |                   |
            | id=20&port=9876   | ,id=20,port=9876  |

    @rest
    Scenario: omit required field
        When I query POST "/ganglias?id=20"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description               |
            | query     |       | name is a required field. |
        And there is no Ganglia with id=20

    @rest
    Scenario Outline: pass an invalid parameter
        When I query POST "/ganglias?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                       |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['port', 'id', 'name']. |
        And there is no Ganglia with cluster_name="ganglia3"
        And there is no Ganglia with id=4

        Examples:
            | query                 |
            | name=ganglia3&foo=bar |
            | foo=bar&name=ganglia3 |
