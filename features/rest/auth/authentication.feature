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

Feature: Authentication required messages
    As an API programmer
    I want to return an error on unauthenticated attempts
    So that access to the API is well-regulated

    @rest
    Scenario: unauthenticated attempt to get all applications
        When I query GET "/applications"
        Then the response code is 401
        And the response contains errors:
            | location  | name      | description                               |
            | header    | cookie    | Authentication required. Please login.    |

    @rest
    Scenario: unauthenticated attempt to get a single application
        Given there is an application with name="app1"
        When I query GET "/applications/app1"
        Then the response code is 401
        And the response contains errors:
            | location  | name      | description                               |
            | header    | cookie    | Authentication required. Please login.    |

    @rest
    Scenario: unauthenticated attempt to add a new application
        When I query POST "/applications?name=app1&job=myjob"
        Then the response code is 401
        And the response contains errors:
            | location  | name      | description                               |
            | header    | cookie    | Authentication required. Please login.    |
        And there is no application with name="app1",id=2

    @rest
    Scenario: unauthenticated attempt to update an application
        Given there is an application with name="app1"
        When I query PUT "/applications/app1?name=newname"
        Then the response code is 401
        And the response contains errors:
            | location  | name      | description                               |
            | header    | cookie    | Authentication required. Please login.    |
        And there is no application with pkg_name="newname",id=2

    @rest
    Scenario: unauthenticated attempt to get all packages for an application
        Given there is an application with name="app1"
        When I query GET "/applications/app1/packages"
        Then the response code is 401
        And the response contains errors:
            | location  | name      | description                               |
            | header    | cookie    | Authentication required. Please login.    |

    @rest
    Scenario: unauthenticated attempt to get a specific package for an application
        Given there is an application with name="app1"
        And there is a package with version="1",revision="1"
        When I query GET "/applications/app1/packages/1/1"
        Then the response code is 401
        And the response contains errors:
            | location  | name      | description                               |
            | header    | cookie    | Authentication required. Please login.    |

    @rest
    Scenario: unauthenticated attempt to get all projects
        When I query GET "/projects"
        Then the response code is 401
        And the response contains errors:
            | location  | name      | description                               |
            | header    | cookie    | Authentication required. Please login.    |

    @rest
    Scenario: unauthenticated attempt to get a specific projects
        Given there is a project with name="proj1"
        When I query GET "/projects/proj1"
        Then the response code is 401
        And the response contains errors:
            | location  | name      | description                               |
            | header    | cookie    | Authentication required. Please login.    |

    @rest
    Scenario: unauthenticated attempt to post a project
        When I query POST "/projects?name=proj1"
        Then the response code is 401
        And the response contains errors:
            | location  | name      | description                               |
            | header    | cookie    | Authentication required. Please login.    |
        And there is no project with name="proj1"

    @rest
    Scenario: unauthenticated attempt to put a project
        Given there is a project with name="proj1"
        When I query PUT "/projects/proj1?name=proj2"
        Then the response code is 401
        And the response contains errors:
            | location  | name      | description                               |
            | header    | cookie    | Authentication required. Please login.    |
        And there is no project with name="proj2"
