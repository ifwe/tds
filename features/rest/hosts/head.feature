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

Feature: HEAD host(s) from the REST API
    As a developer
    I want to test my GET query
    So that I can be sure my query is not malformed

    Background:
        Given I have a cookie with user permissions
        And there is an environment with name="dev"

    @rest
    Scenario: no hosts
        When I query HEAD "/hosts"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario Outline: get a host that doesn't exist
        When I query HEAD "/hosts/<select>"
        Then the response code is 404
        And the response body is empty

        Examples:
            | select    |
            | noexist   |
            | 500       |

    @rest
    Scenario: get all hosts
        Given there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
        When I query HEAD "/hosts"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario Outline: get a single host by name
        Given there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
        When I query HEAD "/hosts/<host>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | host  |
            | host1 |
            | host2 |

    @rest
    Scenario Outline: get a single host by ID
        Given there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
        When I query HEAD "/hosts/<id>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | id    |
            | 1     |
            | 2     |

    @rest
    Scenario Outline: specify limit and/or last queries
        Given there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
            | host3 | dev   |
            | host4 | dev   |
            | host5 | dev   |
            | host6 | dev   |
        When I query HEAD "/hosts?limit=<limit>&start=<start>"
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
        Given there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
        When I query HEAD "/hosts?<query>"
        Then the response code is 422
        And the response body is empty

        Examples:
            | query             |
            | foo=bar           |
            | limit=10&foo=bar  |
            | foo=bar&start=2   |
