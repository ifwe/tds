# Copyright 2016 Ifwe Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
            | name          | param         | props                     | query                                                                 |
            | name          | name          | id=3,env="prod"           | name=development&short_name=prod&domain=foobar.com&zone_id=1          |
            | short_name    | short_name    | id=3,env="prod"           | name=production&short_name=dev&domain=foobar.com&zone_id=1            |
            | prefix        | prefix        | id=3,env="prod"           | name=production&short_name=dev&domain=foobar.com&zone_id=1&prefix=d   |
            | domain        | domain        | id=3,env="prod"           | name=production&short_name=dev&domain=devexample.com&zone_id=1        |
