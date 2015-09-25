Feature: POST environment(s) from the REST API
    As an admin
    I want to add a new environment
    So that it can be used in the database

    Background:
        Given I have a cookie with admin permissions
        And there is an environment with name="dev"
        And there is an environment with name="staging"

    @rest
    Scenario: add a new environment
        When I query POST "/environments?name=production&short_name=prod&domain=foobar.com&zone_id=1"
        Then the response code is 201
        And the response is an object with name="production",short_name="prod",domain="foobar.com",zone_id=1
        And there is an environment with environment="production",env="prod",domain="foobar.com",zone_id=1

    @rest
    Scenario: omit required field
        When I query POST "/environments?name=production&domain=foobar.com&zone_id=1"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                       |
            | query     |       | short_name is a required field.   |
        And there is no environment with environment="production",domain="foobar.com",zone_id=1

    @rest
    Scenario Outline: attempt to violate a unique constraint
        When I query POST "/environments?<query>"
        Then the response code is 409
        And the response contains errors:
            | location  | name      | description                                                                   |
            | query     | <name>    | Unique constraint violated. An environment with this <param> already exists.  |
        And there is no environment with <props>

        Examples:
            | name          | param         | props                     | query                                                                     |
            | id            | ID            | environment="production"  | id=1&name=production&short_name=prod&domain=foobar.com&zone_id=1          |
            | name          | name          | id=3,env="prod"           | name=development&short_name=prod&domain=foobar.com&zone_id=1              |
            | short_name    | short_name    | id=3,env="prod"           | name=production&short_name=dev&domain=foobar.com&zone_id=1                |
            | prefix        | prefix        | id=3,env="prod"           | name=production&short_name=dev&domain=foobar.com&zone_id=1&prefix=d       |
            | domain        | domain        | id=3,env="prod"           | name=production&short_name=dev&domain=devexample.com&zone_id=1            |
