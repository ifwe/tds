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

Feature: GET host(s) from the REST API
    As a developer
    I want information on hosts
    So that I can be informed of the current state of the database

    Background:
        Given I have a cookie with user permissions
        And there is an environment with name="dev"

    @rest
    Scenario: no hosts
        When I query GET "/hosts"
        Then the response code is 200
        And the response is a list of 0 items

    @rest
    Scenario Outline: get a host that doesn't exist
        When I query GET "/hosts/<select>"
        Then the response code is 404
        And the response contains errors:
            | location  | name          | description                           |
            | path      | name_or_id    | Host with <descript> does not exist.  |

        Examples:
            | select    | descript      |
            | noexist   | name noexist  |
            | 500       | ID 500        |

    @rest
    Scenario: get all hosts
        Given there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
        When I query GET "/hosts"
        Then the response code is 200
        And the response is a list of 2 items
        And the response list contains objects:
            | name  |
            | host1 |
            | host2 |

    @rest
    Scenario: get all hosts with select query
        Given there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
        When I query GET "/hosts?select=name"
        Then the response code is 200
        And the response is a list of 2 items
        And the response list contains objects:
            | name  |
            | host1 |
            | host2 |
        And the response list objects do not contain attributes id,cage,environment_id,dc_id,rack,state,console_port,cab,distribution,tier_id,spec_id

    @rest
    Scenario Outline: get a single host
        Given there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
        When I query GET "/hosts/<host>"
        Then the response code is 200
        And the response is an object with name="<name>"

        Examples:
            | host  | name  |
            | host1 | host1 |
            | host2 | host2 |
            | 1     | host1 |
            | 2     | host2 |

    @rest
    Scenario Outline: get a single host with select query
        Given there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
        When I query GET "/hosts/<host>?select=name"
        Then the response code is 200
        And the response is an object with name="<name>"
        And the response list objects do not contain attributes id,cage,environment_id,dc_id,rack,state,console_port,cab,distribution,tier_id,spec_id

        Examples:
            | host  | name  |
            | host1 | host1 |
            | host2 | host2 |
            | 1     | host1 |
            | 2     | host2 |

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
        When I query GET "/hosts?limit=<limit>&start=<start>"
        Then the response code is 200
        And the response is a list of <num> items
        And the response list contains id range <min> to <max>

        Examples:
            | limit | start | num   | min   | max   |
            |       |       | 6     | 1     | 6     |
            |       | 2     | 5     | 2     | 6     |
            | 10    |       | 6     | 1     | 6     |
            | 4     | 1     | 4     | 1     | 4     |

    @rest
    Scenario Outline: specify unknown query
        Given there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
        When I query GET "/hosts?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                               |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['limit', 'select', 'start'].   |

        Examples:
            | query             |
            | foo=bar           |
            | limit=10&foo=bar  |
            | foo=bar&start=2   |
