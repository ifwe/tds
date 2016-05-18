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

Feature: GET HipChat(s) from the REST API
    As an admin
    I want information on HipChat objects
    So that I can be informed of the current state of the database

    Background:
        Given I have a cookie with user permissions
        And there is a HipChat with room_name="hipchat1"
        And there is a HipChat with room_name="hipchat2"

    @rest
    Scenario Outline: get a Ganglia that doesn't exist
        When I query GET "/hipchats/<select>"
        Then the response code is 404
        And the response contains errors:
            | location  | name          | description                               |
            | path      | name_or_id    | Hipchat with <descript> does not exist.   |

        Examples:
            | select    | descript      |
            | noexist   | name noexist  |
            | 500       | ID 500        |

    @rest
    Scenario: get all HipChats
        When I query GET "/hipchats"
        Then the response code is 200
        And the response is a list of 2 items
        And the response list contains objects:
            | name      |
            | hipchat1  |
            | hipchat2  |

    @rest
    Scenario: get all HipChats with select query
        When I query GET "/hipchats?select=name"
        Then the response code is 200
        And the response is a list of 2 items
        And the response list contains objects:
            | name      |
            | hipchat1  |
            | hipchat2  |
        And the response list objects do not contain attributes id

    @rest
    Scenario Outline: get a single HipChat
        When I query GET "/hipchats/<select>"
        Then the response code is 200
        And the response is an object with name="hipchat1"

        Examples:
            | select    |
            | hipchat1  |
            | 1         |

    @rest
    Scenario Outline: get a single HipChat with select query
        When I query GET "/hipchats/<select>?select=name"
        Then the response code is 200
        And the response is an object with name="hipchat1"
        And the response object does not contain attributes id

        Examples:
            | select    |
            | hipchat1  |
            | 1         |

    @rest
    Scenario Outline: specify limit and/or last queries
        Given there is a HipChat with room_name="hipchat3"
        And there is a HipChat with room_name="hipchat4"
        And there is a HipChat with room_name="hipchat5"
        When I query GET "/hipchats?limit=<limit>&start=<start>"
        Then the response code is 200
        And the response is a list of <num> items
        And the response list contains id range <min> to <max>

        Examples:
            | limit | start | num   | min   | max   |
            |       |       | 5     | 1     | 5     |
            |       | 2     | 4     | 2     | 5     |
            | 10    |       | 5     | 1     | 5     |
            | 4     | 1     | 4     | 1     | 4     |
