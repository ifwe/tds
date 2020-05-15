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

Feature: PUT host(s) from the REST API
    As an admin
    I want to update a host
    So that database information reflects the current environment state

    Background:
        Given I have a cookie with admin permissions
        And there is an environment with name="dev"
        And there is a deploy target with name="tier1"
        And there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
        And the hosts are associated with the deploy target
        And there is an environment with name="stage"
        And there is a deploy target with name="tier2"

    @rest
    Scenario Outline: update a host
        When I query PUT "/hosts/<select>?<params>"
        Then the response code is 200
        And the response is an object with <props>

        Examples:
            | select    | params                            | props                                                 |
            | host1     |                                   | name="host1",id=1                                     |
            | 1         |                                   | name="host1",id=1                                     |
            | host1     | rack=100&cage=20&environment_id=2 | name="host1",id=1,rack=100,cage=20,environment_id=2   |
            | 1         | rack=100&cage=20&environment_id=2 | name="host1",id=1,rack=100,cage=20,environment_id=2   |
            | host1     | tier_id=2                         | name="host1",id=1,tier_id=2                           |
            | 1         | tier_id=2                         | name="host1",id=1,tier_id=2                           |
            | host1     | name=host3                        | name="host3",id=1                                     |
            | 1         | name=host3                        | name="host3",id=1                                     |

    @rest
    Scenario Outline: attempt to update a host that doesn't exist
        When I query PUT "/hosts/<select>?name=host100"
        Then the response code is 404
        And the response contains errors:
            | location  | name          | description                           |
            | path      | name_or_id    | Host with <descript> does not exist.  |
        And there is no host with name="host100"

        Examples:
            | select    | descript      |
            | noexist   | name noexist  |
            | 500       | ID 500        |

    @rest
    Scenario Outline: pass an invalid parameter
        When I query PUT "/hosts/<select>?name=host100&foo=bar"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                                                                                                       |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['cab', 'cage', 'elevation', 'distribution', 'environment_id', 'name', 'rack', 'state', 'tier_id'].  |

        Examples:
            | select    |
            | host1     |
            | 1         |
