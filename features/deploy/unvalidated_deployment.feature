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

Feature: attempt promote with unvalidated deployment in previous env
    As a developer
    I want to be notified when I attempt to promote an unvalidated deployment
    So that I don't uninentionally break software in an important env

    Background:
        Given I have "stage" permissions
        And there are environments
            | name   |
            | dev    |
            | stage  |
        And I am in the "stage" environment
        And there is a project with name="proj"
        And there is an application with name="myapp"
        And there is a deploy target with name="the-apptype"
        And there is a package with version="121"
        And the package is deployed on the deploy targets in the "dev" env
        And there are hosts:
            | name          | env   |
            | dprojhost01   | dev   |
            | dprojhost02   | dev   |
            | sprojhost01   | stage |
            | sprojhost02   | stage |
        And the deploy target is a part of the project-application pair
        And the hosts are associated with the deploy target

    Scenario: Attempt promote for a single host
        When I run "deploy promote myapp 121 --hosts sprojhost01"
        Then the output has "Application "myapp", version "121" is not validated in the previous environment for tier "the-apptype", skipping..."
        And the output has "Nothing to do."
        And there is no deployment with id=2
        And there is no tier deployment with deployment_id=2
        And there is no host deployment with deployment_id=2

    Scenario: Attempt to promote for a tier
        When I run "deploy promote myapp 121 --apptypes the-apptype"
        Then the output has "Application "myapp", version "121" is not validated in the previous environment for tier "the-apptype", skipping..."
        And the output has "Nothing to do."
        And there is no deployment with id=2
        And there is no tier deployment with deployment_id=2
        And there is no host deployment with deployment_id=2
