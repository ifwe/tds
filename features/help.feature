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
Feature: Help switches
    As a user
    I want help text
    So that I can learn how to use the program

    Scenario Outline: help
        When I run "<command> <switch>"
        Then the output has "usage:"

        Examples:
            | command                    | switch    |
            |                            | -h        |
            | project                    | -h        |
            | project add                | -h        |
            | project delete             | -h        |
            | project list               | -h        |
            | application                | -h        |
            | application add            | -h        |
            | application add-apptype    | -h        |
            | application delete         | -h        |
            | application delete-apptype | -h        |
            | application list           | -h        |
            | package                    | -h        |
            | package add                | -h        |
            | package delete             | -h        |
            | package list               | -h        |
            | deploy                     | -h        |
            | deploy invalidate          | -h        |
            | deploy promote             | -h        |
            | deploy restart             | -h        |
            | deploy rollback            | -h        |
            | deploy show                | -h        |
            | deploy validate            | -h        |
            |                            | --help    |
            | project                    | --help    |
            | project add                | --help    |
            | project delete             | --help    |
            | project list               | --help    |
            | application                | --help    |
            | application add            | --help    |
            | application add-apptype    | --help    |
            | application delete         | --help    |
            | application delete-apptype | --help    |
            | application list           | --help    |
            | package                    | --help    |
            | package add                | --help    |
            | package delete             | --help    |
            | package list               | --help    |
            | deploy                     | --help    |
            | deploy invalidate          | --help    |
            | deploy promote             | --help    |
            | deploy restart             | --help    |
            | deploy rollback            | --help    |
            | deploy show                | --help    |
            | deploy validate            | --help    |
