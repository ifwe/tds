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
            | query     | props         |
            |           |               |
            | port=9876 | ,port=9876    |

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
            | location  | name  | description                                                   |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['name', 'port'].   |
        And there is no Ganglia with cluster_name="ganglia3"
        And there is no Ganglia with id=4

        Examples:
            | query                 |
            | name=ganglia3&foo=bar |
            | foo=bar&name=ganglia3 |
