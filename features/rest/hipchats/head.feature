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

Feature: HEAD HipChat(s) from the REST API
    As a user
    I want to test my GET query
    So that I can be sure my query is not malformed

    Background:
        Given I have a cookie with user permissions
        And there is a HipChat with room_name="hipchat1"
        And there is a HipChat with room_name="hipchat2"

    @rest
    Scenario Outline: get a Ganglia that doesn't exist
        When I query HEAD "/hipchats/<select>"
        Then the response code is 404
        And the response body is empty

        Examples:
            | select    |
            | noexist   |
            | 500       |

    @rest
    Scenario: get all HipChats
        When I query HEAD "/hipchats"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario Outline: get a single HipChat
        When I query HEAD "/hipchats/<select>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | select    |
            | hipchat1  |
            | 1         |

    @rest
    Scenario Outline: specify limit and/or last queries
        Given there is a HipChat with room_name="hipchat3"
        And there is a HipChat with room_name="hipchat4"
        And there is a HipChat with room_name="hipchat5"
        When I query HEAD "/hipchats?limit=<limit>&start=<start>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | limit | start |
            |       |       |
            |       | 2     |
            | 10    |       |
            | 4     | 1     |
