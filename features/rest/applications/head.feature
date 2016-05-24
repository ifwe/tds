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

Feature: HEAD application(s) from the REST API
    As a developer
    I want to test my GET query
    So that I can be sure my query is not malformed

    Background:
        Given I have a cookie with user permissions

    @rest
    Scenario: no applications
        When I query HEAD "/applications"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario Outline: get an application that doesn't exist
        When I query HEAD "/applications/<select>"
        Then the response code is 404
        And the response body is empty

        Examples:
            | select    |
            | noexist   |
            | 500       |

    @rest
    Scenario: get all applications
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
            | app3  |
        When I query HEAD "/applications"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario Outline: get a single application by name
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
            | app3  |
        When I query HEAD "/applications/<app>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | app   |
            | app1  |
            | app2  |
            | app3  |

    @rest
    Scenario Outline: get a single application by ID
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
            | app3  |
        When I query HEAD "/applications/<id>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | id    |
            | 1     |
            | 2     |
            | 3     |

    @rest
    Scenario Outline: pass select query for individual application
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
            | app3  |
        When I query HEAD "/applications/app1?select=<select>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | select    |
            | name      |
            | name,job  |

    @rest
    Scenario Outline: pass select query for collection of applications
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
            | app3  |
        When I query HEAD "/applications?select=<select>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | select    |
            | name      |
            | name,job  |

    @rest
    Scenario: pass invalid attr to select
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
            | app3  |
        When I query HEAD "/applications?select=foo"
        Then the response code is 400
        And the response body is empty

    @rest
    Scenario Outline: specify limit and/or last queries
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
            | app3  |
            | app4  |
            | app5  |
        When I query HEAD "/applications?limit=<limit>&start=<start>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | limit | start |
            |       |       |
            |       | 2     |
            | 10    |       |
            | 4     | 1     |

    @rest
    Scenario Outline: specify unknown query
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
        When I query HEAD "/applications?<query>"
        Then the response code is 422
        And the response body is empty

        Examples:
            | query             |
            | foo=bar           |
            | limit=10&foo=bar  |
            | foo=bar&start=2   |
