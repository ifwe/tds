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

Feature: HEAD tier-hipchat relationship(s) from the REST API
    As a user
    I want to test my GET query
    So that I can be sure my query is not malformed

    Background:
        Given I have a cookie with user permissions
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are hipchat rooms:
            | room_name |
            | hipchat1  |
            | hipchat2  |
        And the deploy target "tier1" is associated with the hipchat "hipchat1"
        And the deploy target "tier1" is associated with the hipchat "hipchat2"

    @rest
    Scenario: get hipchats for a tier that doesn't exist
        When I query HEAD "/tiers/foo/hipchats"
        Then the response code is 404
        And the response body is empty

    @rest
    Scenario: get all hipchats associated with a tier
        When I query HEAD "/tiers/tier1/hipchats"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario: get a HipChat that doesn't exist
        When I query HEAD "/tiers/tier1/hipchats/hipchat500"
        Then the response code is 404
        And the response body is empty

    @rest
    Scenario Outline: get a specific hipchat
        When I query HEAD "/tiers/tier1/hipchats/<select>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | select    |
            | hipchat1  |
            | 1         |

    @rest
    Scenario: pass a parameter
        When I query HEAD "/tiers/tier1/hipchats?limit=10&start=10"
        Then the response code is 422
        And the response body is empty
