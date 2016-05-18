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

Feature: parameter validation (common errors)
    As a developer
    I want to ensure invalid parameter situations are caught
    So I can feel safe and secure

    Background:
        Given I have "dev" permissions
        And there is an environment with name="dev"
        And I am in the "dev" environment

    # NOTE: This test will go away once multiple package definitions
    #       are supported
    Scenario: multiple package definitions found for an application
        Given there is an application with name="myapp",path="app-foo"
        And there is an application with name="myapp",path="app-bar"
        When I run "deploy show myapp"
        Then the output is "Multiple definitions for application found, please file ticket in JIRA for TDS"
