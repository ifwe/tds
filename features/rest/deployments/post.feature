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

Feature: POST deployment(s) from the REST API
    As a developer
    I want to add deployments
    So that I can deploy my software to the environment

    Background:
        Given I have a cookie with user permissions

    @rest
    Scenario: post a deployment
        When I query POST "/deployments"
        Then the response code is 201
        And the response is an object with id=1,status="pending",user="testuser"
        And there is a deployment with id=1,status="pending",user="testuser",duration=0

    @rest
    Scenario: pass delay option
        When I query POST "/deployments?delay=10"
        Then the response code is 201
        And the response is an object with id=1,status="pending",user="testuser",delay=10
        And there is a deployment with id=1,status="pending",user="testuser",delay=10,duration=0

    @rest
    Scenario: attempt to set the status while posting
        When I query POST "/deployments?status=queued"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                   |
            | query     | status    | Status must be pending for new deployments.   |
        And there is no deployment with id=1
        And there is no deployment with status="queued"

    @rest
    Scenario: attempt to use force parameter
        When I query POST "/deployments?status=queued&force=1"
        Then the response code is 403
        And the response contains errors:
            | location  | name  | description                                       |
            | query     | force | Force query is only supported for PUT requests.   |
        And there is no deployment with id=1
        And there is no deployment with status="queued"
