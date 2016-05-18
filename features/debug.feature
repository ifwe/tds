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

Feature: Debug switches
    As a user
    I want debug information
    So that I can find out what's going on deeper in the program

    Background:
        Given there are environments
            | name   |
            | dev    |
            | stage  |

    Scenario Outline: debug package list
        Given I have "dev" permissions
        And I am in the "dev" environment
        And there are applications:
            | name |
            | bar  |
            | foo  |
        When I run "<switch> package list"
        Then the output has "DEBUG"

    Examples:
        | switch |
        | -v     |
        | -vv    |
        | -vvv   |

    Scenario Outline: debug deploy promote
        Given I have "stage" permissions
        And I am in the "stage" environment
        And there is a project with name="proj"
        And there is a deploy target with name="the-apptype"
        And there is an application with name="app1"
        And there is a package with version="123"
        And the package is deployed on the deploy targets in the "dev" env
        And the package has been validated in the "development" environment
        And there are hosts:
            | name          | env   |
            | dprojhost01   | dev   |
            | dprojhost02   | dev   |
            | sprojhost01   | stage |
            | sprojhost02   | stage |
        And the deploy target is a part of the project-application pair
        And the hosts are associated with the deploy target
        When I run "<switch> deploy promote proj 123 <targets>"
        Then the output has "DEBUG"

        Examples:
            | switch | targets                           |
            | -v     | --hosts sprojhost01 sprojhost02   |
            | -vv    | --hosts sprojhost01 sprojhost02   |
            | -vvv   | --hosts sprojhost01 sprojhost02   |
            | -v     | --all-apptypes                    |
            | -vv    | --all-apptypes                    |
            | -vvv   | --all-apptypes                    |
            | -v     | --apptypes the-apptype            |
            | -vv    | --apptypes the-apptype            |
            | -vvv   | --apptypes the-apptype            |

    Scenario Outline: debug deploy validate
        Given I have "dev" permissions
        And I am in the "dev" environment
        And there is a project with name="proj"
        And there is a deploy target with name="foo"
        And there is an application with name="app1"
        And there is a package with version="123"
        And there are hosts:
            | name          |
            | projhost01    |
            | projhost02    |
        And the deploy target is a part of the project-application pair
        And the hosts are associated with the deploy target
        And the package is deployed on the deploy target
        When I run "<switch> deploy validate proj 123 --apptype foo"
        Then the output has "DEBUG"

        Examples:
            | switch |
            | -v     |
            | -vv    |
            | -vvv   |

    Scenario Outline: debug deploy invalidate
        Given I have "dev" permissions
        And I am in the "dev" environment
        And there is a project with name="proj"
        And there is an application with name="app1"
        And there is a package with version="123"
        And there is a deploy target with name="foo"
        And the deploy target is a part of the project-application pair
        And the package is deployed on the deploy targets
        And the package has been validated
        When I run "<switch> deploy invalidate proj 123 --apptype foo"
        Then the output has "DEBUG"

        Examples:
            | switch |
            | -v     |
            | -vv    |
            | -vvv   |
