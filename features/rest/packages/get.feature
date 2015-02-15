Feature: GET package(s) from the REST API
    As a developer
    I want information on packages
    So that I can be informed of the current state of the database

    Background:
        Given there are applications:
            | name  |
            | app1  |
            | app2  |
        And there are packages:
            | version   | revision  |
            | 1         | 2         |
            | 2         | 1         |

    @rest
    Scenario Outline: no application
        When I query GET "/applications/<select>/<pkg_select>"
        Then the response code is 404
        And the response contains errors:
            | location  | name          | description                                   |
            | path      | name_or_id    | Application with <descript> does not exist.   |

        Examples:
            | select    | pkg_select    | descript      |
            | noexist   | packages      | name noexist  |
            | noexist   | packages/1/1  | name noexist  |
            | 5         | packages      | ID 5          |
            | 5         | packages/1/1  | ID 5          |

    @rest
    Scenario Outline: no packages
        When I query GET "/applications/<select>/packages"
        Then the response code is 200
        And the response is a list of 0 items

        Examples:
            | select    |
            | app1      |
            | 2         |

    @rest
    Scenario Outline: get all packages for an application
        When I query GET "/applications/<select>/packages"
        Then the response code is 200
        And the response is a list of 2 items
        And the response list contains objects:
            | version   | revision  |
            | 1         | 2         |
            | 2         | 1         |

        Examples:
            | select    |
            | app2      |
            | 3         |

    @rest
    Scenario Outline: get a package that doesn't exist for an application that does exist
        When I query GET "/applications/<select>/packages/<ver>/<rev>"
        Then the response code is 404
        And the response contains errors:
            | location  | name      | description                                                                           |
            | path      | revision  | Package with version <ver> and revision <rev> does not exist for this application.    |

        Examples:
            | select    | ver   | rev   |
            | app2      | 5     | 1     |
            | 3         | 5     | 1     |
            | app2      | 1     | 5     |
            | 3         | 1     | 5     |

    @rest
    Scenario Outline: get a specific package
        When I query GET "/applications/<select>/packages/<ver>/<rev>"
        Then the response code is 200
        And the response is an object with version="<ver>",revision="<rev>"

        Examples:
            | select    | ver   | rev   |
            | app2      | 1     | 2     |
            | 3         | 1     | 2     |
            | app2      | 2     | 1     |
            | 3         | 2     | 1     |
