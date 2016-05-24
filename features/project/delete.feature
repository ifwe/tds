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

Feature: project delete project
    As an administrator
    I want to delete a project
    To clean up things that don't exist anymore

    @no_db
    Scenario: too few arguments
        When I run "project delete"
        Then the output has "usage:"

    @no_db
    Scenario: invalid arguments
        When I run "project delete --foo"
        Then the output has "usage:"

    Scenario: for admin with existing project
        Given I have "admin" permissions
        And there is a project with name="proj"
        When I run "project delete proj"
        Then the output has "Project "proj" was successfully deleted"
        And there is no project with name="proj"

    Scenario: for admin with non-existing project
        Given I have "admin" permissions
        When I run "project delete proj"
        Then the output has "Project does not exist: proj"
        And there is no project with name="proj"
