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

Feature: project add project
    As an administrator
    I want to add projects to the repository
    So that developers can deploy the projects with TDS

    Background:
        Given I have "admin" permissions

    @no_db
    Scenario: too few arguments
        When I run "project add"
        Then the output has "usage:"

    @no_db
    Scenario: too many arguments
        When I run "project add proj foo"
        Then the output has "usage:"

    Scenario: add new project
        When I run "project add proj"
        Then there is a project with name="proj"
        And the output has "Created proj:"
        And the output describes a project with name="proj"

    Scenario: add project that already exists
        Given there is a project with name="proj"
        When I run "project add proj"
        Then the output is "Project already exists: proj"
