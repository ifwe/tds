Feature: PUT environment(s) from the REST API
    As an admin
    I want to change an environment
    So that the database reflects the current state of the environment (hehe)

    Background:
        Given I have a cookie with admin permissions
        And there is an environment with name="dev"
        And there is an environment with name="staging"

    @rest
    Scenario: update an environment
        When I query PUT "/environments/development?name=newname"
        Then the response code is 200
        And the response is an object with name="newname",id=1
        And there is an environment with environment="newname",id=1
        And there is no environment with environment="development",id=1

    @rest
    Scenario Outline: attempt to violate a unique constraint
        When I query PUT "/environments/staging?<query>"
        Then the response code is 409
        And the response contains errors:
            | location  | name      | description                                                                       |
            | query     | <name>    | Unique constraint violated. Another environment with this <param> already exists. |
        And there is no environment with <props>
        And there is an environment with environment="staging",env="staging",prefix="s",zone_id=2,domain="stagingexample.com"

        Examples:
            | name          | param         | props                     | query                                                                     |
            | id            | ID            | environment="production"  | id=1&name=production&short_name=prod&domain=foobar.com&zone_id=1          |
            | name          | name          | id=3,env="prod"           | name=development&short_name=prod&domain=foobar.com&zone_id=1              |
            | short_name    | short_name    | id=3,env="prod"           | name=production&short_name=dev&domain=foobar.com&zone_id=1                |
            | prefix        | prefix        | id=3,env="prod"           | name=production&short_name=dev&domain=foobar.com&zone_id=1&prefix=d       |
            | domain        | domain        | id=3,env="prod"           | name=production&short_name=dev&domain=devexample.com&zone_id=1            |
