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

Feature: Real-life application usage
    As a user
    I want to have multiple deploy targets with multiple applications
    So that I can have a real live website that's neat

    Background:
        Given I have "dev" permissions
        And there is an environment with name="dev"
        And I am in the "dev" environment

        And there is a project with name="solr"
        And there is an application with name="solr-app"
        And there are packages:
            | version |
            | 123     |
            | 124     |
            | 125     |
        And there is a deploy target with name="solrsearch"
        And there is a host with name="ss1"
        And the host is associated with the deploy target
        And there is a host with name="ss2"
        And the host is associated with the deploy target
        And there is a host with name="ss3"
        And the host is associated with the deploy target
        And there is an application with name="tagconfig"
        And there are packages:
            | version |
            | 456     |
            | 457     |
            | 458     |
        And there is a deploy target with name="solrbrowse"
        And there is a host with name="sb1"
        And the host is associated with the deploy target
        And there is a host with name="sb2"
        And the host is associated with the deploy target
        And there is a host with name="sb3"
        And the host is associated with the deploy target
        And the deploy targets are a part of the project-application pairs

        And the package with name="tagconfig",version="456" is deployed on the deploy target with name="solrsearch"
        And the package with name="tagconfig",version="457" is deployed on the deploy target with name="solrbrowse"

        And the package with name="solr-app",version="123" is deployed on the deploy target with name="solrsearch"
        And the package with name="solr-app",version="124" is deployed on the deploy target with name="solrbrowse"

    Scenario: other app to deploy target with tagconfig and another app
        When I run "deploy promote solr-app 124 --apptypes solrsearch --detach"
        Then the output has "Deployment ready for installer daemon, disconnecting now."
        And there is a deployment with id=2,status="queued",duration=0
        And there is a tier deployment with deployment_id=2,app_id=2,status="pending",package_id=2,environment_id=1,duration=0
        And there is a host deployment with deployment_id=2,host_id=1,status="pending",package_id=2,duration=0
        And there is a host deployment with deployment_id=2,host_id=2,status="pending",package_id=2,duration=0
        And there is a host deployment with deployment_id=2,host_id=3,status="pending",package_id=2,duration=0

    Scenario: tagconfig to deploy target with tagconfig and another app
        When I run "deploy promote tagconfig 457 --apptypes solrsearch --detach"
        Then the output has "Deployment ready for installer daemon, disconnecting now."
        And there is a deployment with id=2,status="queued",duration=0
        And there is a tier deployment with deployment_id=2,app_id=2,status="pending",package_id=5,environment_id=1,duration=0
        And there is a host deployment with deployment_id=2,host_id=1,status="pending",package_id=5,duration=0
        And there is a host deployment with deployment_id=2,host_id=2,status="pending",package_id=5,duration=0
        And there is a host deployment with deployment_id=2,host_id=3,status="pending",package_id=5,duration=0

    # TODO: Definitely need more tests here!!!
