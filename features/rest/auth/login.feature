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

Feature: Login
    As a developer
    I want to login
    So that I can have access to interact with the REST API

    @rest
    Scenario Outline: insufficient parameters
        When I POST "{<body>}" to "/login"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                                                                                               |
            | body      |       | Could not parse body as valid JSON. Body must be a JSON object with attributes "username" and "password". |

        Examples:
            | body              |
            |                   |
            | "password": "bar" |
            | "username": "foo" |

    @rest
    Scenario: invalid credentials
        When I POST "{"username": "horsefeathers", "password": "hensteeth"}" to "/login"
        Then the response code is 401
        And the response does not contain a cookie
        And the response contains errors:
            | location  | name      | description                                                                   |
            | query     | user      | Authentication failed. Please check your username and password and try again. |

    @rest @ldap_off
    Scenario: LDAP server not accessible
        When I POST "{"username": "horsefeathers", "password": "hensteeth"}" to "/login"
        Then the response code is 500
        And the response contains errors:
            | location  | name  | description                       |
            | url       |       | Could not connect to LDAP server. |

    @rest
    Scenario: valid credentials
        When I POST "{"username": "testuser", "password": "secret"}" to "/login"
        Then the response code is 200
        And the response contains a cookie

    @rest
    Scenario Outline: specify method permissions
        When I POST "{"username": "testuser", "password": "secret", "methods": "<methods>"}" to "/login"
        Then the response code is 200
        And the response contains a cookie with methods=<methods>

        Examples:
            | methods           |
            | GET               |
            | GET+POST          |
            | GET+POST+DELETE   |

    @rest
    Scenario: attempt to get a wildcard cookie without authorization
        When I POST "{"username": "testuser", "password": "secret", "wildcard": true}" to "/login"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                   |
            | body      | wildcard  | Insufficient authorization. You are not authorized to get wildcard cookies.   |

    @rest
    Scenario: get a wildcard cookie
        Given "testuser" is a wildcard user in the REST API
        When I POST "{"username": "testuser", "password": "secret", "wildcard": true}" to "/login"
        Then the response code is 200
        And the response contains a cookie

    @rest
    Scenario: get an eternal cookie
        Given "testuser" is an eternal user in the REST API
        When I POST "{"username": "testuser", "password": "secret", "eternal": true}" to "/login"
        Then the response code is 200
        And the response contains a cookie with eternal=True

    @rest
    Scenario: attempt to get an eternal cookie without authorization
        When I POST "{"username": "testuser", "password": "secret", "eternal": true}" to "/login"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                   |
            | body      | eternal   | Insufficient authorization. You are not authorized to get eternal cookies.    |

    @rest
    Scenario: attempt to get an env-specific cookie for an environment that doesn't exist
        When I POST "{"username": "testuser", "password": "secret", "environments": "1"}" to "/login"
        Then the response code is 400
        And the response contains errors:
            | location  | name          | description                           |
            | body      | environments  | Could not find environment with ID 1. |

    @rest
    Scenario Outline: get an env-specific cookie
        Given there is an environment with name="dev"
        And there is an environment with name="stage"
        And there is an environment with name="prod"
        When I POST "{"username": "testuser", "password": "secret", "environments": "<envs>"}" to "/login"
        Then the response code is 200
        And the response contains a cookie with environments=<envs>

        Examples:
            | envs  |
            | 1     |
            | 1+2   |
            | 1+2+3 |
