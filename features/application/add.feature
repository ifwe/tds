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

Feature: application add application job_name [--deploy_type] [--arch] [--build_type] [--build_host]
    As an administrator
    I want to add applications to the system
    So that developers can create packages for the application

    Background:
        Given I have "admin" permissions

    @no_db
    Scenario: too few arguments
        When I run "application add myapp"
        Then the output has "usage:"

    @no_db
    Scenario: invalid arguments
        When I run "application add myapp myjob --foo"
        Then the output has "usage:"

    Scenario: adding application
        When I run "application add myapp myjob"
        Then there is an application
            | key         | value         |
            | name        | myapp         |
            | deploy_type | rpm           |
            | arch        | noarch        |
            | build_type  | jenkins       |
            | build_host  | ci.tagged.com |
            | path        | myjob         |

    Scenario: adding application with invalid architecture
        When I run "application add myapp myjob --arch no-exist-arch"
        Then the output has "Invalid architecture: no-exist-arch. Should be one of: i386, noarch, x86_64"

    Scenario: adding application with invalid build type
        When I run "application add myapp myjob --build-type no-exist-build-type"
        Then the output has "Invalid build type: no-exist-build-type. Should be one of: developer, hudson, jenkins"

    Scenario: adding application that already exists
        Given there is an application with pkg_name="myapp"
        When I run "application add myapp myjob"
        Then the output has "Application already exists: myapp"
