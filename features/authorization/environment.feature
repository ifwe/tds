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

@no_db
Feature: Authorization roles - environment
    As a user
    I want authorization limitations
    So that I can't break things I'm not supposed to

    Scenario Outline:
        Given I am in the "dev" environment
        And I have "no" permissions
        When I run "<command>"
        Then the output is "You do not have the appropriate permissions to run this command. Contact your manager."

        Examples:
            | command                   |
            | application list          |
            | deploy invalidate foo 123 |
            | deploy show foo           |
            | deploy validate foo 123   |
            | deploy promote foo 123    |
            | deploy rollback foo       |
            | deploy restart foo        |
            | package list              |
            | package add foo 123       |
            | package delete foo 123    |
            | project list              |
