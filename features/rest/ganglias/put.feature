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

Feature: PUT Ganglia(s) from the REST API
    As an admin
    I want to change a Ganglia object
    So that the database reflects the current state of the environment

    Background:
        Given I have a cookie with admin permissions
        And there is a Ganglia with cluster_name="ganglia1"
        And there is a Ganglia with cluster_name="ganglia2"

    @rest
    Scenario Outline: update a Ganglia object that doesn't exist
        When I query PUT "/ganglias/<select>?name=newname"
        Then the response code is 404
        And the response contains errors:
            | location  | name          | description                               |
            | path      | name_or_id    | Ganglia with <descript> does not exist.   |
        And there is no Ganglia with cluster_name="newname"

        Examples:
            | select    | descript      |
            | noexist   | name noexist  |
            | 500       | ID 500        |

    @rest
    Scenario Outline: update a Ganglia object
        When I query PUT "/ganglias/<select>?name=newname"
        Then the response code is 200
        And the response is an object with name="newname",id=2
        And there is a Ganglia with cluster_name="newname",id=2

        Examples:
            | select    |
            | ganglia1  |
            | 2         |

    @rest
    Scenario Outline: pass an invalid parameter
        When I query PUT "/ganglias/<select>?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                   |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['name', 'port'].   |
        And there is a Ganglia with cluster_name="ganglia1",id=2

        Examples:
            | select    | query                 |
            | ganglia1  | foo=bar               |
            | 2         | foo=bar               |
            | ganglia1  | name=newname&foo=bar  |
            | 2         | name=newname&foo=bar  |
            | ganglia1  | foo=bar&name=newname  |
            | 2         | foo=bar&name=newname  |

    @rest
    Scenario Outline: attempt to violate a unique constraint
        When I query PUT "/ganglias/<select>?name=ganglia2"
        Then the response code is 409
        And the response contains errors:
            | location  | name  | description                                                                   |
            | query     | name  | Unique constraint violated. Another ganglia with this name already exists.    |

        Examples:
            | select    |
            | ganglia1  |
            | 2         |
