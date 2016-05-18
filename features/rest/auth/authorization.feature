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

Feature: Authorization required messages
    As an API programmer
    I want to prevent users from doing things they are not authorized to do
    So that major catastrophes can be prevented

    Background:
        Given I have a cookie with user permissions

    #TODO: Add DELETE tests for relevant paths.
    @rest
    Scenario: unauthorized attempt to POST a new application
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
            | app3  |
        When I query POST "/applications?name=app4&job=myjob"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                   |
            | header    | cookie    | Admin authorization required. Please contact someone in SiteOps to perform this operation for you. |
        And there is no application with pkg_name="app4"
        And there is no application with path="myjob"

    @rest
    Scenario: unauthorized attempt to PUT an application
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
        When I query PUT "/applications/app1?name=app3&job=myjob"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                   |
            | header    | cookie    | Admin authorization required. Please contact someone in SiteOps to perform this operation for you. |
        And there is no application with pkg_name="app3"
        And there is no application with path="myjob"
        And there is an application with pkg_name="app1"

    @rest
    Scenario: unauthorized attempt to POST a project
        Given there are projects:
            | name  |
            | proj1 |
            | proj2 |
        When I query POST "/projects?name=proj3"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                   |
            | header    | cookie    | Admin authorization required. Please contact someone in SiteOps to perform this operation for you. |
        And there is no project with name="proj3"

    @rest
    Scenario: unauthorized attempt to PUT a project
        Given there are projects:
            | name  |
            | proj1 |
            | proj2 |
        When I query PUT "/projects/proj1?name=proj3"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                   |
            | header    | cookie    | Admin authorization required. Please contact someone in SiteOps to perform this operation for you. |
        And there is no project with name="proj3"
        And there is a project with name="proj1"

    @rest
    Scenario: unauthorized attempt to POST a tier
        Given there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        When I query POST "/tiers?name=tier3"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                   |
            | header    | cookie    | Admin authorization required. Please contact someone in SiteOps to perform this operation for you. |
        And there is no deploy target with name="tier3"

    @rest
    Scenario: unauthorized attempt to PUT a tier
        Given there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        When I query PUT "/tiers/tier1?name=tier3"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                   |
            | header    | cookie    | Admin authorization required. Please contact someone in SiteOps to perform this operation for you. |
        And there is no deploy target with name="tier3"
        And there is a deploy target with name="tier1"

    @rest
    Scenario: unauthorized attempt to POST a host
        Given there is an environment with name="dev"
        And there is a deploy target with name="tier1"
        And there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
        And the hosts are associated with the deploy target
        When I query POST "/hosts?name=host3&tier_id=2"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                   |
            | header    | cookie    | Admin authorization required. Please contact someone in SiteOps to perform this operation for you. |
        And there is no host with name="host3"

    @rest
    Scenario: unauthorized attempt to PUT a host
        Given there is an environment with name="dev"
        And there is a deploy target with name="tier1"
        And there are hosts:
            | name  | env   |
            | host1 | dev   |
            | host2 | dev   |
        And the hosts are associated with the deploy target
        When I query PUT "/hosts/host1?name=host3"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                   |
            | header    | cookie    | Admin authorization required. Please contact someone in SiteOps to perform this operation for you. |
        And there is no host with name="host3"
        And there is a host with name="host1"

    @rest
    Scenario: unauthorized attempt to POST a Ganglia
        Given there is a Ganglia with cluster_name="ganglia1"
        And there is a Ganglia with cluster_name="ganglia2"
        When I query POST "/ganglias?name=ganglia3"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                   |
            | header    | cookie    | Admin authorization required. Please contact someone in SiteOps to perform this operation for you. |
        And there is no Ganglia with cluster_name="ganglia3"

    @rest
    Scenario: unauthorized attempt to PUT a Ganglia
        Given there is a Ganglia with cluster_name="ganglia1"
        And there is a Ganglia with cluster_name="ganglia2"
        When I query PUT "/ganglias/ganglia1?name=ganglia3"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                   |
            | header    | cookie    | Admin authorization required. Please contact someone in SiteOps to perform this operation for you. |
        And there is no Ganglia with cluster_name="ganglia3"
        And there is a Ganglia with cluster_name="ganglia1"
