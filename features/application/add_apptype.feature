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

Feature: application add-apptype application project target(s)
    As an administrator
    I want to add deploy targets to project/application pairs
    So I can deploy packages to the targets

    Background:
        Given I have "admin" permissions
        And there is a project with name="proj"
        And there is an application with name="myapp"
        And there is a deploy target with name="targ1"

    # TODO: should these arg checks be in another file that checks overall
    #       cli behavior?
    Scenario: too few arguments
        When I run "application add-apptype myapp proj"
        Then the output has "usage:"

    Scenario: add a target to a project/application pair with an application that doesn't exist
        When I run "application add-apptype badapp proj targ"
        Then the output is "Application does not exist: badapp"

    Scenario: add a target to a project/application pair with a project that doesn't exist
        When I run "application add-apptype myapp badproj targ"
        Then the output is "Project does not exist: badproj"

    Scenario: add a target that doesn't exist to a project/application pair
        When I run "application add-apptype myapp proj badtarg"
        Then the output is "Deploy target does not exist: badtarg"

    Scenario: add a target to a project/application pair
        When I run "application add-apptype myapp proj targ1"
        Then the output is "Future deployments of "myapp" in "proj" will affect "targ1""
        And the deploy target is a part of the project-application pair

    Scenario: add a target to a project/application pair again
        Given the deploy target is a part of the project-application pair
        When I run "application add-apptype myapp proj targ1"
        Then the output is "Apptype "targ1" is already a part of the project "proj" and application "myapp" pair"

    Scenario: add multiple targets to a project/application pair where one target doesn't exist
        When I run "application add-apptype myapp proj targ1 badtarg"
        Then the output is "Deploy target does not exist: badtarg"

    Scenario: add multiple targets to a project/application pair
        Given there is a deploy target with name="targ2"
        When I run "application add-apptype myapp proj targ1 targ2"
        Then the output is "Future deployments of "myapp" in "proj" will affect "targ1", "targ2""
        Then the deploy targets are a part of the project-application pair
