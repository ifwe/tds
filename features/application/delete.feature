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

Feature: application delete application
    As an administrator
    I want to delete an application
    To clean up things that don't exist anymore

    Background:
        Given I have "admin" permissions
        And there is an environment with name="dev"

    Scenario: too few arguments
        When I run "application delete"
        Then the output has "usage:"

    Scenario: invalid arguments
        When I run "application delete myapp --foo"
        Then the output has "usage:"

    Scenario: for admin with non-existing project
        When I run "application delete myapp"
        Then the output has "Application does not exist: myapp"
        And there is no application with name="myapp"

    Scenario: for admin with existing application with no targets
        Given there is an application with name="myapp"
        When I run "application delete myapp"
        Then the output has "Application "myapp" was successfully deleted"
        And there is no application with name="myapp"

    Scenario: for admin with existing application with targets
        Given I am in the "dev" environment
        And there is an application with name="myapp"
        And there is a project with name="proj"
        And there is a deploy target with name="the-apptype"
        And the deploy target is a part of the project-application pair
        When I run "application delete myapp"
        Then the output has "Application "myapp" has associated targets: the-apptype"
        And there is an application with name="myapp"
