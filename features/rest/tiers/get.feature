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

Feature: GET app tier(s) from the REST API
    As a developer
    I want information on app tiers
    So that I can be informed of the current state of the database

    Background:
        Given I have a cookie with user permissions

    @rest
    Scenario: no app tiers
        When I query GET "/tiers"
        Then the response code is 200
        And the response is a list of 0 items

    @rest
    Scenario Outline: get an app tier that doesn't exist
        When I query GET "/tiers/<select>"
        Then the response code is 404
        And the response contains errors:
            | location  | name          | description                           |
            | path      | name_or_id    | Tier with <descript> does not exist.  |

        Examples:
            | select    | descript      |
            | noexist   | name noexist  |
            | 500       | ID 500        |

    @rest
    Scenario: get all tiers
        Given there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        When I query GET "/tiers"
        Then the response code is 200
        And the response is a list of 2 items
        And the response list contains objects:
            | name  |
            | tier1 |
            | tier2 |

    @rest
    Scenario: get all tiers with select query
        Given there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        When I query GET "/tiers?select=name"
        Then the response code is 200
        And the response is a list of 2 items
        And the response list contains objects:
            | name  |
            | tier1 |
            | tier2 |
        And the response list objects do not contain attributes id,status,puppet_class,description,host_base,distribution,ganglia_id

    @rest
    Scenario Outline: get a single tier by name
        Given there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        When I query GET "/tiers/<tier>"
        Then the response code is 200
        And the response is an object with name="<tier>"

        Examples:
            | tier  |
            | tier1 |
            | tier2 |

    @rest
    Scenario Outline: get a single tier by name with select query
        Given there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        When I query GET "/tiers/<tier>?select=name"
        Then the response code is 200
        And the response is an object with name="<tier>"
        And the response object does not contain attributes id,status,puppet_class,description,host_base,distribution,ganglia_id

        Examples:
            | tier  |
            | tier1 |
            | tier2 |

    @rest
    Scenario Outline: get a single tier by ID
        Given there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        When I query GET "/tiers/<id>"
        Then the response code is 200
        And the response is an object with id=<id>

        Examples:
            | id    |
            | 1     |
            | 2     |
            | 3     |

    @rest
    Scenario Outline: specify limit and/or last queries
        Given there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there is a deploy target with name="tier3"
        And there is a deploy target with name="tier4"
        And there is a deploy target with name="tier5"
        When I query GET "/tiers?limit=<limit>&start=<start>"
        Then the response code is 200
        And the response is a list of <num> items
        And the response list contains id range <min> to <max>

        Examples:
            | limit | start | num   | min   | max   |
            |       |       | 5     | 2     | 6     |
            |       | 2     | 5     | 2     | 6     |
            | 10    |       | 5     | 2     | 6     |
            | 4     | 1     | 4     | 2     | 5     |

    @rest
    Scenario Outline: specify unknown query
        Given there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        When I query GET "/tiers?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                               |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['limit', 'select', 'start'].   |

        Examples:
            | query             |
            | foo=bar           |
            | limit=10&foo=bar  |
            | foo=bar&start=2   |
