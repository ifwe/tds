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

Feature: HEAD package(s) from the REST API by ID
    As a developer
    I want to test my GET query
    So that I can be sure my query is not malformed

    Background:
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
        And there are packages:
            | version   | revision  |
            | 1         | 2         |
            | 2         | 1         |
            | 2         | 2         |
            | 2         | 3         |
            | 3         | 1         |
        And I have a cookie with user permissions

    @rest
    Scenario: get all packages
        When I query HEAD "/packages"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario: get a package by ID
        When I query HEAD "/packages/2"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario: get a package that doesn't exist
        When I query HEAD "/packages/500"
        Then the response code is 404
        And the response body is empty

    @rest
    Scenario: specify unknown query
        When I query HEAD "/packages?foo=bar"
        Then the response code is 422
        And the response body is empty

    @rest
    Scenario Outline: specify limit and/or last queries
        When I query HEAD "/packages?limit=<limit>&start=<start>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | limit | start |
            |       |       |
            |       | 1     |
            | 10    |       |
            | 4     | 1     |
            |       |       |
            |       | 2     |
            | 10    |       |
            | 4     | 1     |
