Feature: Update (PUT) package on REST API
    As a developer
    I want to update information for one of my packages
    So that the database has the proper information

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

    @rest
    Scenario Outline: update a package for an application that doesn't exist
        When I query PUT "/applications/<select>/packages/1/2"
        Then the response code is 404
        And the response contains errors:
            | location  | name          | description                                   |
            | path      | name_or_id    | Application with <descript> does not exist.   |

        Examples:
            | select    | descript      |
            | noexist   | name noexist  |
            | 500       | ID 500        |

    @rest
    Scenario Outline: update a package that doesn't exist for an application that does
        When I query PUT "/applications/<select>/packages/<ver>/<rev>"
        Then the response code is 404
        And the response contains errors:
            | location  | name      | description                                                                           |
            | path      | revision  | Package with version <ver> and revision <rev> does not exist for this application.    |

        Examples:
            | select    | ver   | rev   |
            | app1      | 3     | 500   |
            | 2         | 3     | 500   |
            | app1      | 500   | 1     |
            | 2         | 500   | 1     |

    @rest
    Scenario Outline: pass an invalid parameter
        When I query PUT "/applications/<select>/packages/2/3?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                                                                   |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['status', 'builder', 'version', 'id', 'revision']. |
        And there is a package with version=2,revision=3

        Examples:
            | select    | query                 |
            | app2      | foo=bar               |
            | 3         | foo=bar               |
            | app2      | version=10&foo=bar    |
            | 3         | version=10&foo=bar    |
            | app2      | foo=bar&version=10    |
            | 3         | foo=bar&version=10    |

    @rest
    Scenario Outline: update a package
        When I query PUT "/applications/<select>/packages/2/3?version=10&revision=50"
        Then the response code is 200
        And the response is an object with version="10",revision="50"
        And there is a package with version=10,revision=50

        Examples:
            | select    |
            | app2      |
            | 3         |

    @rest
    Scenario Outline: attemp to violate a unique constraint
        When I query PUT "/applications/<select>/packages/2/3?<query>"
        Then the response code is 409
        And the response contains errors:
            | location  | name      | description                                                                                                       |
            | query     | <name>    | Unique constraint violated. Another package for this application with this version and revision already exists.   |
        And there is a package with version=2,revision=3

        Examples:
            | select    | name      | query                 |
            | app2      | revision  | revision=2            |
            | 3         | revision  | revision=2            |
            | app2      | version   | version=2&revision=2  |
            | 3         | version   | version=2&revision=2  |
