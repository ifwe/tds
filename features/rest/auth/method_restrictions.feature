Feature: Method restrictions on cookie
    As an admin
    I want to provide cookies with specific method privileges
    So that I can provide cookies for programs in a safer manner

    @rest
    Scenario: authorized GET
        Given I have a cookie with user permissions and methods=GET
        And there is a project with name="myproj"
        When I query GET "/projects/myproj"
        Then the response code is 200
        And the response is an object with name="myproj"

    @rest
    Scenario: authorized HEAD
        Given I have a cookie with user permissions and methods=GET
        And there is a project with name="myproj"
        When I query HEAD "/projects/myproj"
        Then the response code is 200
        And the response body is empty

    @rest
    Scenario Outline: unauthorized POST
        Given I have a cookie with user permissions and methods=<methods>
        When I query POST "/deployments"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                                           |
            | header    | cookie    | Insufficient authorization. This cookie only has permissions for the following privileged methods: [<method_list>].   |

        Examples:
            | methods       | method_list       |
            | GET           | 'GET'             |
            | GET+PUT       | 'GET', 'PUT'      |
            | GET+DELETE    | 'DELETE', 'GET'   |

    @rest
    Scenario Outline: authorized POST
        Given I have a cookie with user permissions and methods=<methods>
        When I query POST "/deployments"
        Then the response code is 201
        And the response is an object with id=1,status="pending"
        And there is a deployment with id=1,status="pending"

        Examples:
            | methods           |
            | POST              |
            | GET+POST          |
            | DELETE+POST       |
            | PUT+POST+DELETE   |

    @rest
    Scenario Outline: unauthorized DELETE
        Given there are deployments:
            | id    | user  | status    |
            | 1     | foo   | pending   |
        And I have a cookie with user permissions and methods=<methods>
        When I query DELETE "/deployments/1"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                                           |
            | header    | cookie    | Insufficient authorization. This cookie only has permissions for the following privileged methods: [<method_list>].   |

        Examples:
            | methods       | method_list           |
            | GET           | 'GET'                 |
            | GET+PUT       | 'GET', 'PUT'          |
            | GET+POST+PUT  | 'GET', 'POST', 'PUT'  |

    @rest
    Scenario Outline: authorized DELETE
        Given there are deployments:
            | id    | user  | status    |
            | 1     | foo   | pending   |
        And I have a cookie with user permissions and methods=<methods>
        When I query DELETE "/deployments/1"
        Then the response code is 200
        And the response is an object with id=1,user="foo",status="pending"
        And there is no deployment with id=1

        Examples:
            | methods           |
            | DELETE            |
            | DELETE+GET        |
            | POST+DELETE+GET   |
