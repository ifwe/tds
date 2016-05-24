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

Feature: POST app tier(s) from the REST API
    As an admin
    I want to add a new app tier
    So that developers can deploy to it using TDS

    Background:
        Given I have a cookie with admin permissions
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"

    @rest
    Scenario Outline: add a new tier
        When I query POST "/tiers?name=tier3&distribution=centos7.1&<params>"
        Then the response code is 201
        And the response is an object with name="tier3",distribution="centos7.1"<props>
        And there is a deploy target with name="tier3",distribution="centos7.1"

        Examples:
            | params                    | props                         |
            |                           |                               |
            | status=inactive           | ,status="inactive"            |
            | puppet_class=cls          | ,puppet_class="cls"           |

    @rest
    Scenario Outline: omit required fields
        When I query POST "/tiers?<params>"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description               |
            | query     |       | name is a required field. |
        And there is no deploy target with id=4

        Examples:
            | params                    |
            |                           |
            | status=inactive           |

    @rest
    Scenario Outline: pass an invalid parameter
        When I query POST "/tiers?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                                                                                   |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['distribution', 'ganglia_id', 'ganglia_name', 'name', 'puppet_class', 'status'].   |
        And there is no deploy target with name="tier3"
        And there is no deploy target with id=4

        Examples:
            | query                                     |
            | name=tier3&foo=bar&distribution=centos7.1 |
            | foo=bar&distribution=centos7.1&name=tier3 |

    @rest
    Scenario: attempt to violate a unique constraint
        When I query POST "/tiers?name=tier2&distribution=centos7.1"
        Then the response code is 409
        And the response contains errors:
            | location  | name  | description                                                       |
            | query     | name  | Unique constraint violated. A tier with this name already exists. |

    @rest
    Scenario: pass a non-integer for an integer param
        When I query POST "/tiers?name=tier3&ganglia_id=3.1415&distribution=centos7.1"
        Then the response code is 400
        And the response contains errors:
            | location  | name          | description                                                                   |
            | query     | ganglia_id    | Validation failed: Value 3.1415 for argument ganglia_id is not an integer.    |
        And there is no deploy target with name="tier3"
        And there is no deploy target with id=4

    @rest
    Scenario: pass a Ganglia ID for a Ganglia entry that doesn't exist
        When I query POST "/tiers?name=tier3&ganglia_id=500&distribution=centos7.1"
        Then the response code is 400
        And the response contains errors:
            | location  | name          | description                           |
            | query     | ganglia_id    | No Ganglia object with ID 500 exists. |
        And there is no deploy target with name="tier3"

    @rest
    Scenario: pass an invalid status
        When I query POST "/tiers?name=tier3&status=foo&distribution=centos7.1"
        Then the response code is 400
        And the response contains errors:
            | location  | name      | description                                                                               |
            | query     | status    | Validation failed: Value foo for argument status must be one of: ['active', 'inactive'].  |
        And there is no deploy target with name="tier3"
