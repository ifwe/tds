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
Feature: Authorization roles
    As a user
    I want authorization limitations
    So that I can't break things I'm not supposed to

    Scenario Outline:
        Given I am in the "dev" environment
        And I have "dev" permissions
        When I run "<command>"
        Then the output is "You do not have the appropriate permissions to run this command. Contact your manager."

        Examples:
            | command                                      |
            | application add myapp myjob                  |
            | application delete myapp                     |
            | application add-apptype myapp proj targ      |
            | application delete-apptype myapp proj targ   |
            | project add proj                             |
            | project delete proj                          |
