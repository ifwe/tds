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

Feature: generate_cookie script
    As an administrator
    I want to generate cookies for use by services
    So that user input is not required by those services

    Background:
        Given "testuser" is an eternal user in the REST API
        And "testuser" is a wildcard user in the REST API

    @rest
    Scenario: generate and use an eternal wildcard cookie for the user
        Given I change cookie life to 1
        When I run "generate_cookie testuser any --eternal"
        And I wait 3 seconds
        And I use the generated cookie
        And I query GET "/projects"
        Then the response code is 200

    @rest
    Scenario: generate and use an expired wildcard cookie
        Given I change cookie life to 1
        When I run "generate_cookie testuser any"
        And I wait 3 seconds
        And I use the generated cookie
        And I query GET "/projects"
        Then the response code is 419
        And the response contains errors:
            | location  | name      | description                                               |
            | header    | cookie    | Cookie has expired or is invalid. Please reauthenticate.  |

    @rest
    Scenario: generate and use a wildcard cookie for the user
        When I run "generate_cookie testuser any"
        And I use the generated cookie
        And I query GET "/projects"
        Then the response code is 200

    @rest
    Scenario Outline: generate and use a cookie in unauthorized restrictions
        Given there is an environment with name="dev"
        And there is an environment with name="staging"
        And there is an environment with name="prod"
        And there is a project with name="proj1"
        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | pending   |
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are applications:
            | name  |
            | app1  |
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
        And the tier "tier1" is associated with the application "app1" for the project "proj1"
        When I run "generate_cookie testuser any --environment_ids=<envs>"
        And I use the generated cookie
        And I query POST "/tier_deployments?deployment_id=1&tier_id=2&environment_id=3&package_id=1"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                                   |
            | header    | cookie    | Insufficient authorization. This cookie only has permissions for the following environment IDs: [<env_list>]. |

        Examples:
            | envs  | env_list  |
            | 1     | 1         |
            | 2     | 2         |
            | 1,2   | 1, 2      |

    @rest
    Scenario Outline: generate and use a cookie in authorized environment
        Given there is an environment with name="dev"
        And there is an environment with name="staging"
        And there is an environment with name="prod"
        And there is a project with name="proj1"
        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | pending   |
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are applications:
            | name  |
            | app1  |
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
        And the tier "tier1" is associated with the application "app1" for the project "proj1"
        When I run "generate_cookie testuser any --environment_ids=<envs>"
        And I use the generated cookie
        And I query POST "/tier_deployments?deployment_id=1&tier_id=2&environment_id=1&package_id=1"
        Then the response code is 201
        And the response is an object with id=1,deployment_id=1,tier_id=2,environment_id=1,package_id=1
        And there is a tier deployment with id=1,deployment_id=1,app_id=2,environment_id=1,package_id=1

        Examples:
            | envs  | env_list  |
            | 1     | 1         |
            | 1,2   | 1, 2      |

    @rest
    Scenario Outline: generate and use a cookie with authorized method
        When I run "generate_cookie testuser any --methods=<methods>"
        And I use the generated cookie
        And I query GET "/projects"
        Then the response code is 200

        Examples:
            | methods   |
            | GET       |
            | GET,POST  |

    @rest
    Scenario Outline: generate and use a cookie with unauthorized method
        When I run "generate_cookie testuser any --methods=<methods>"
        And I use the generated cookie
        And I query POST "/deployments"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                                           |
            | header    | cookie    | Insufficient authorization. This cookie only has permissions for the following privileged methods: [<method_list>].   |

        Examples:
            | methods       | method_list       |
            | GET           | 'GET'             |
            | GET,PUT       | 'GET', 'PUT'      |
            | GET,DELETE    | 'DELETE', 'GET'   |
