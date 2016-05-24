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

Feature: Update (PUT) application on REST API
    As a developer
    I want to update information for one of my applications
    So that the database has the proper information

    Background:
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
            | app3  |
        And I have a cookie with admin permissions

    @rest
    Scenario Outline: update an application that doesn't exist
        When I query PUT "/applications/<select>?name=newname"
        Then the response code is 404
        And the response contains errors:
            | location  | name          | description                                   |
            | path      | name_or_id    | Application with <descript> does not exist.   |
        And there is no application with pkg_name="newname"

        Examples:
            | select    | descript      |
            | noexist   | name noexist  |
            | 500       | ID 500        |

    @rest
    Scenario Outline: update an application
        When I query PUT "/applications/<select>?name=newname"
        Then the response code is 200
        And the response is an object with name="newname",id=2
        And there is an application with pkg_name="newname",id=2

        Examples:
            | select    |
            | app1      |
            | 2         |

    @rest
    Scenario: update application repository field
        When I query PUT "/applications/app1?repository=https://www.example.org/repo/foo/bar"
        Then the response code is 200
        And the response is an object with name="app1",id=2,repository="https://www.example.org/repo/foo/bar"
        And there is an application with pkg_name="app1",id=2,repository="https://www.example.org/repo/foo/bar"

    @rest
    Scenario Outline: pass an invalid parameter
        When I query PUT "/applications/<select>?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                                                                                                                       |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['arch', 'build_host', 'build_type', 'deploy_type', 'env_specific', 'job', 'name', 'repository', 'validation_type'].    |
        And there is an application with pkg_name="app1",id=2

        Examples:
            | select    | query                     |
            | app1      | foo=bar                   |
            | 2         | foo=bar                   |
            | app1      | pkg_name=newname&foo=bar  |
            | 2         | pkg_name=newname&foo=bar  |
            | app1      | foo=bar&pkg_name=newname  |
            | 2         | foo=bar&pkg_name=newname  |

    @rest
    Scenario Outline: attempt to violate a unique constraint
        When I query PUT "/applications/<select>?name=app2"
        Then the response code is 409
        And the response contains errors:
            | location  | name  | description                                                                       |
            | query     | name  | Unique constraint violated. Another application with this name already exists.    |
        And there is an application with pkg_name="app1",id=2

        Examples:
            | select    |
            | app1      |
            | 2         |
