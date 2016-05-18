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

Feature: HEAD app tier(s) from the REST API
    As a developer
    I want to test my GET query
    So that I can be sure my query is not malformed

    Background:
        Given I have a cookie with user permissions

    @rest
    Scenario: no app tiers
        When I query HEAD "/tiers"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario Outline: get an app tier that doesn't exist
        When I query HEAD "/tiers/<select>"
        Then the response code is 404
        And the response body is empty

        Examples:
            | select    |
            | noexist   |
            | 500       |

    @rest
    Scenario: get all tiers
        Given there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        When I query HEAD "/tiers"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario Outline: get a single tier by name
        Given there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        When I query HEAD "/tiers/<tier>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | tier  |
            | tier1 |
            | tier2 |

    @rest
    Scenario Outline: get a single tier by ID
        Given there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        When I query HEAD "/tiers/<id>"
        Then the response code is 200
        And the response body is empty

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
        When I query HEAD "/tiers?limit=<limit>&start=<start>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | limit | start |
            |       |       |
            |       | 2     |
            | 10    |       |
            | 4     | 1     |

    @rest
    Scenario Outline: specify unknown query
        Given there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        When I query HEAD "/tiers?<query>"
        Then the response code is 422
        And the response body is empty

        Examples:
            | query             |
            | foo=bar           |
            | limit=10&foo=bar  |
            | foo=bar&start=2   |
