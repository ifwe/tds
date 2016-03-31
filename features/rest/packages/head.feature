Feature: HEAD package(s) from the REST API
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
    Scenario Outline: no application
        When I query HEAD "/applications/<select>/<pkg_select>"
        Then the response code is 404
        And the response body is empty

        Examples:
            | select    | pkg_select    |
            | noexist   | packages      |
            | noexist   | packages/1/1  |
            | 5         | packages      |
            | 5         | packages/1/1  |

    @rest
    Scenario Outline: no packages
        When I query HEAD "/applications/<select>/packages"
        Then the response code is 200
        And the response body is empty

        Examples:
            | select    |
            | app1      |
            | 2         |

    @rest
    Scenario Outline: get all packages for an application
        When I query HEAD "/applications/<select>/packages"
        Then the response code is 200
        And the response body is empty

        Examples:
            | select    |
            | app2      |
            | 3         |

    @rest
    Scenario Outline: get a package that doesn't exist for an application that does exist
        When I query HEAD "/applications/<select>/packages/<ver>/<rev>"
        Then the response code is 404
        And the response body is empty

        Examples:
            | select    | ver   | rev   |
            | app2      | 5     | 1     |
            | app2      | 1     | 5     |
            | 3         | 5     | 1     |
            | 3         | 1     | 5     |

    @rest
    Scenario Outline: get a specific package
        When I query HEAD "/applications/<select>/packages/<ver>/<rev>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | select    | ver   | rev   |
            | app2      | 1     | 2     |
            | app2      | 2     | 1     |
            | 3         | 1     | 2     |
            | 3         | 2     | 1     |

    @rest
    Scenario Outline: specify unknown query
        When I query HEAD "/applications/<select>/packages?<query>"
        Then the response code is 422
        And the response body is empty

        Examples:
            | select    | query             |
            | app2      | foo=bar           |
            | app2      | limit=10&foo=bar  |
            | app2      | foo=bar&start=2   |
            | 3         | foo=bar           |
            | 3         | limit=10&foo=bar  |
            | 3         | foo=bar&start=2   |

    @rest
    Scenario Outline: specify limit and/or last queries
        When I query HEAD "/applications/<select>/packages?limit=<limit>&start=<start>"
        Then the response code is 200
        And the response body is empty

        Examples:
            | select    | limit | start |
            | app2      |       |       |
            | app2      |       | 1     |
            | app2      | 10    |       |
            | app2      | 4     | 1     |
            | 3         |       |       |
            | 3         |       | 2     |
            | 3         | 10    |       |
            | 3         | 4     | 1     |
