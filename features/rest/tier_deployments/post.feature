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

Feature: POST tier deployment(s) from the REST API
    As a developer
    I want to add tier deployments
    So that I can put my software on tiers

    Background:
        Given I have a cookie with user permissions
        And there is an application with pkg_name="app1"
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
            | 1         | 2         |
        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | pending   |
        And there are projects:
            | name  |
            | proj1 |
        And there is an environment with name="dev"
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And the tier "tier1" is associated with the application "app1" for the project "proj1"
        And the tier "tier2" is associated with the application "app1" for the project "proj1"

    @rest
    Scenario: post a tier deployment
        When I query POST "/tier_deployments?deployment_id=1&tier_id=2&environment_id=1&package_id=1"
        Then the response code is 201
        And the response is an object with deployment_id=1,tier_id=2,id=1,user="testuser",environment_id=1,package_id=1
        And there is a tier deployment with deployment_id=1,app_id=2,id=1,user="testuser",environment_id=1,package_id=1,duration=0

    @rest
    Scenario: post a tier deployment for a tier with hosts
        Given there is an environment with name="staging"
        And there are hosts:
            | name  | env       | app_id    |
            | host1 | dev       | 2         |
            | host2 | dev       | 2         |
            | host3 | staging   | 2         |
            | host4 | dev       | 3         |
        When I query POST "/tier_deployments?deployment_id=1&tier_id=2&environment_id=1&package_id=1"
        Then the response is an object with deployment_id=1,tier_id=2,id=1,user="testuser",environment_id=1,package_id=1
        And there is a tier deployment with deployment_id=1,app_id=2,id=1,user="testuser",environment_id=1,package_id=1,duration=0
        And there is a host deployment with deployment_id=1,host_id=1,user="testuser",package_id=1,duration=0
        And there is a host deployment with deployment_id=1,host_id=2,user="testuser",package_id=1,duration=0
        And there is no host deployment with deployment_id=1,host_id=3,user="testuser",package_id=1
        And there is no host deployment with deployment_id=1,host_id=4,user="testuser",package_id=1

    @rest
    Scenario: omit required field
        When I query POST "/tier_deployments?deployment_id=1"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                           |
            | query     |       | tier_id is a required field.          |
            | query     |       | environment_id is a required field.   |
            | query     |       | package_id is a required field.       |
        And there is no tier deployment with deployment_id=1
        And there is no tier deployment with id=1

    @rest
    Scenario Outline: attempt to set the status to not pending
        When I query POST "/tier_deployments?deployment_id=1&tier_id=2&environment_id=1&package_id=1&status=<status>"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                       |
            | query     | status    | Status must be pending for new tier deployments.  |
        And there is no tier deployment with deployment_id=1,app_id=2,status="<status>",environment_id=1,package_id=1
        And there is no tier deployment with id=1

        Examples:
            | status        |
            | inprogress    |
            | failed        |
            | ok            |

    @rest
    Scenario: pass a tier_id for a tier that doesn't exist
        When I query POST "/tier_deployments?deployment_id=1&tier_id=500&environment_id=1&package_id=1"
        Then the response code is 400
        And the response contains errors:
            | location  | name      | description                   |
            | query     | tier_id   | No tier with ID 500 exists.   |
        And there is no tier deployment with deployment_id=1,app_id=500,environment_id=1,package_id=1
        And there is no tier deployment with id=1

    @rest
    Scenario: pass an environment_id for an environment that doesn't exist
        When I query POST "/tier_deployments?deployment_id=1&tier_id=2&environment_id=500&package_id=1"
        Then the response code is 400
        And the response contains errors:
            | location  | name              | description                           |
            | query     | environment_id    | No environment with ID 500 exists.    |
        And there is no tier deployment with deployment_id=1,app_id=2,environment_id=500,package_id=1
        And there is no tier deployment with id=1

    @rest
    Scenario: pass a package_id for a package that doesn't exist
        When I query POST "/tier_deployments?deployment_id=1&tier_id=2&environment_id=1&package_id=500"
        Then the response code is 400
        And the response contains errors:
            | location  | name          | description                       |
            | query     | package_id    | No package with ID 500 exists.    |
        And there is no tier deployment with deployment_id=1,app_id=2,environment_id=1,package_id=500
        And there is no tier deployment with id=1

    @rest
    Scenario: attempt to violate (deployment_id, tier_id, package_id) unique together constraint
        Given there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 1     | 1             | 2         | pending   | foo   | 1                 | 1             |
        When I query POST "/tier_deployments?deployment_id=1&tier_id=2&environment_id=1&package_id=1"
        Then the response code is 409
        And the response contains errors:
            | location  | name          | description                                                                                                               |
            | query     | package_id    | ('deployment_id', 'tier_id', 'package_id') are unique together. A tier deployment with these attributes already exists.   |
        And there is no tier deployment with id=2

    @rest
    Scenario: attempt to add a tier deployment such that its environment conflicts with that of the deployment
        Given there is an environment with name="staging"
        And there are hosts:
            | name  | env       |
            | host1 | staging   |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 1     | 1             | 1         | pending   | foo   | 1             |
        And there is a deploy target with name="tier1"
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 1     | 1             | 1         | pending   | foo   | 2                 | 1             |
        When I query POST "/tier_deployments?deployment_id=1&tier_id=2&environment_id=1&package_id=1"
        Then the response code is 409
        And the response contains errors:
            | location  | name              | description                                                                                                                                                   |
            | query     | environment_id    | Cannot deploy to different environments with same deployment. There is a host deployment associated with this deployment with ID 1 and environment staging.   |
            | query     | environment_id    | Cannot deploy to different environments with same deployment. There is a tier deployment associated with this deployment with ID 1 and environment staging.   |
        And there is no tier deployment with deployment_id=1,app_id=2,environment_id=1

    @rest
    Scenario: attempt to deploy to a tier that isn't associated with the package's application
        Given there is an application with pkg_name="app2"
        And there are packages:
            | version   | revision  |
            | 2         | 3         |
        When I query POST "/tier_deployments?deployment_id=1&tier_id=2&environment_id=1&package_id=3"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                               |
            | query     | tier_id   | Tier tier1 is not associated with the application app2 for any projects.  |
        And there is no tier deployment with package_id=3
        And there is no host deployment with package_id=3
