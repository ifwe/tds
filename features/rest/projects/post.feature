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

Feature: Add (POST) project on REST API
    As a developer
    I want to add a new project
    So that the database has the proper information

    Background:
        Given there are projects:
            | name  |
            | proj1 |
            | proj2 |
            | proj3 |
        And I have a cookie with admin permissions

    @rest
    Scenario: add a new project
        When I query POST "/projects?name=proj4"
        Then the response code is 201
        And the response is an object with name="proj4",id=4
        And there is a project with name="proj4",id=4

    @rest
    Scenario: omit required field
        When I query POST "/projects"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description               |
            | query     |       | name is a required field. |
        And there is no project with id=4

    @rest
    Scenario Outline: pass an invalid parameter
        When I query POST "/projects?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                           |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['name'].   |
        And there is no project with name="proj4"

        Examples:
            | query                |
            | name=proj4&foo=bar   |
            | foo=bar&name=proj4   |

    @rest
    Scenario: attempt to violate a unique constraint
        When I query POST "/projects?name=proj3"
        Then the response code is 409
        And the response contains errors:
            | location  | name  | description                                                           |
            | query     | name  | Unique constraint violated. A project with this name already exists.  |
