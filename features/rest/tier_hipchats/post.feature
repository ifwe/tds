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

Feature: POST tier-hipchat relationship(s) from the REST API
    As a user
    I want to associated a HipChat with a tier
    So that notifications can be sent to that HipChat when changes are made to that tier

    Background:
        Given I have a cookie with user permissions
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are hipchat rooms:
            | room_name |
            | hipchat1  |
            | hipchat2  |
            | hipchat3  |
        And the deploy target "tier1" is associated with the hipchat "hipchat1"
        And the deploy target "tier1" is associated with the hipchat "hipchat2"

    @rest
    Scenario Outline: post a tier-hipchat association
        When I query POST "/tiers/tier1/hipchats?<query>"
        Then the response code is 201
        And the response is an object with name="hipchat3",id=3
        And the deploy target "tier1" is associated with the hipchat "hipchat3"

        Examples:
            | query         |
            | name=hipchat3 |
            | id=3          |

    @rest
    Scenario: post a tier-hipchat association that already exists
        When I query POST "/tiers/tier1/hipchats?name=hipchat2"
        Then the response code is 200
        And the response is an object with name="hipchat2",id=2
        And the deploy target "tier1" is associated with the hipchat "hipchat2"

    @rest
    Scenario Outline: post a tier-hipchat that doesn't exist
        When I query POST "/tiers/tier1/hipchats?<params>"
        Then the response code is 404
        And the response contains errors:
            | location  | name      | description                               |
            | query     | <name>    | Hipchat with <descript> does not exist.   |

        Examples:
            | params            | name  | descript          |
            | name=hipchat500   | name  | name hipchat500   |
            | id=500            | id    | ID 500            |

    @rest
    Scenario: omit required fields
        When I query POST "/tiers/tier1/hipchats?"
        Then the response code is 400
        And the response contains errors:
            | location  | name      | description                                       |
            | query     |           | Either name or ID for the HipChat is required.    |

    @rest
    Scenario: pass an invalid parameter
        When I query POST "/tiers/tier1/hipchats?name=hipchat3&foo=bar"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                               |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['id', 'name']. |
        And the deploy target "tier1" is not associated with the hipchat "hipchat3"
