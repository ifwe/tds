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

Feature: POST HipChat(s) from the REST API
    As an admin
    I want to add a new HipChat object
    So that it can be used in the database

    Background:
        Given I have a cookie with admin permissions
        And there is a HipChat with room_name="hipchat1"
        And there is a HipChat with room_name="hipchat2"

    @rest
    Scenario: add a new HipChat
        When I query POST "/hipchats?name=hipchat3"
        Then the response code is 201
        And the response is an object with name="hipchat3",id=3
        And there is a HipChat with room_name="hipchat3",id=3

    @rest
    Scenario: omit required field
        When I query POST "/hipchats?"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description               |
            | query     |       | name is a required field. |
        And there is no HipChat with id=3

    @rest
    Scenario Outline: pass an invalid parameter
        When I query POST "/hipchats?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                           |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['name'].   |
        And there is no HipChat with room_name="hipchat3"
        And there is no HipChat with id=3

        Examples:
            | query                 |
            | name=hipchat3&foo=bar |
            | foo=bar&name=hipchat3 |
