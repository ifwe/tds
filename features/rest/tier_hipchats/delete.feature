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

Feature: DELETE tier-hipchat relationship(s) from the REST API
    As a user
    I want to disassociate a HipChat from a tier
    So that notifications are no longer sent to that HipChat when changes are made to that tier

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
    Scenario: delete a tier-hipchat association
        When I query DELETE "/tiers/tier1/hipchats/hipchat2"
        Then the response code is 200
        And the response is an object with name="hipchat2",id=2
        And the deploy target "tier1" is not associated with the hipchat "hipchat2"

    @rest
    Scenario: attempt to delete a tier-hipchat association that doesn't exist
        When I query DELETE "/tiers/tier1/hipchats/hipchat3"
        Then the response code is 404
        And the response contains errors:
            | location  | name                  | description                                   |
            | path      | hipchat_name_or_id    | This tier-HipChat association does not exist. |
