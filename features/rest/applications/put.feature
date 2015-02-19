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

    @rest
    Scenario Outline: update an application that doesn't exist
        When I query PUT "/applications/<select>?pkg_name=newname"
        Then the response code is 404
        And the response contains errors:
            | location  | name          | description                                   |
            | path      | name_or_id    | Application with <descript> does not exist.   |

        Examples:
            | select    | descript      |
            | noexist   | name noexist  |
            | 500       | ID 500        |

    @rest
    Scenario Outline: update an application
        When I query PUT "/applications/<select>?pkg_name=newname"
        Then the response code is 200
        And the response is an object with pkg_name="newname",id=2
        And there is an application with pkg_name="newname",id=2

        Examples:
            | select    |
            | app1      |
            | 2         |

    @rest
    Scenario Outline: pass an invalid parameter
        When I query PUT "/applications/<select>?<query>"
        Then the response code is 400
        And the response contains errors:
            | location  | name  | description                                                                                                                                                                                                                                                                       |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['build_host', 'environment_specific', 'applications', 'path', 'packages', 'arch', 'build_type', 'projects', 'deploy_type', 'package_names', 'all_packages', 'name', 'created', 'validation_type', 'id', 'env_specific', 'pkg_name'].   |
        And there is an application with pkg_name="app1",id=2

        Examples:
            | select    | query                     |
            | app1      | foo=bar                   |
            | 2         | foo=bar                   |
            | app1      | pkg_name=newname&foo=bar  |
            | 2         | pkg_name=newname&foo=bar  |
            | app1      | foo=bar&pkg_name=newname  |
            | 2         | foo=bar&pkg_name=newname  |
