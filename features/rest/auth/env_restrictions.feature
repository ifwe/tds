Feature: Restrictions on cookie
    As an admin
    I want to provide cookies with specific environment and/or method privileges
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

    @rest
    Scenario Outline: POST tier deployment to unauthorized environment
        Given there is an environment with name="dev"
        And there is an environment with name="staging"
        And there is an environment with name="prod"
        And there is a project with name="proj1"
        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | pending   |
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are applications:
            | name  |
            | app1  |
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
        And the tier "tier1" is associated with the application "app1" for the project "proj1"
        And I have a cookie with user permissions and environments=<envs>
        When I query POST "/tier_deployments?deployment_id=1&tier_id=2&environment_id=3&package_id=1"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                                   |
            | header    | cookie    | Insufficient authorization. This cookie only has permissions for the following environment IDs: [<env_list>]. |

        Examples:
            | envs  | env_list  |
            | 1     | 1         |
            | 2     | 2         |
            | 1+2   | 1, 2      |

    @rest
    Scenario Outline: POST tier deployment to authorized environment
        Given there is an environment with name="dev"
        And there is an environment with name="staging"
        And there is an environment with name="prod"
        And there is a project with name="proj1"
        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | pending   |
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are applications:
            | name  |
            | app1  |
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
        And the tier "tier1" is associated with the application "app1" for the project "proj1"
        And I have a cookie with user permissions and environments=<envs>
        When I query POST "/tier_deployments?deployment_id=1&tier_id=2&environment_id=1&package_id=1"
        Then the response code is 201
        And the response is an object with id=1,deployment_id=1,tier_id=2,environment_id=1,package_id=1
        And there is a tier deployment with id=1,deployment_id=1,app_id=2,environment_id=1,package_id=1

        Examples:
            | envs  | env_list  |
            | 1     | 1         |
            | 1+2   | 1, 2      |

    @rest
    Scenario Outline: PUT tier deployment to unauthorized environment
        Given there is an environment with name="dev"
        And there is an environment with name="staging"
        And there is an environment with name="prod"
        And there is a project with name="proj1"
        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | pending   |
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are applications:
            | name  |
            | app1  |
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
        And the tier "tier1" is associated with the application "app1" for the project "proj1"
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 1     | 1             | 2         | pending   | foo   | 1                 | 1             |
        And I have a cookie with user permissions and environments=<envs>
        When I query PUT "/tier_deployments/1?environment_id=3"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                                   |
            | header    | cookie    | Insufficient authorization. This cookie only has permissions for the following environment IDs: [<env_list>]. |

        Examples:
            | envs  | env_list  |
            | 1     | 1         |
            | 2     | 2         |
            | 1+2   | 1, 2      |

    @rest
    Scenario: PUT tier deployment to authorized environment
        Given there is an environment with name="dev"
        And there is an environment with name="staging"
        And there is an environment with name="prod"
        And there is a project with name="proj1"
        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | pending   |
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are applications:
            | name  |
            | app1  |
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
        And the tier "tier1" is associated with the application "app1" for the project "proj1"
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 1     | 1             | 2         | pending   | foo   | 1                 | 1             |
        And I have a cookie with user permissions and environments=1+2
        When I query PUT "/tier_deployments/1?environment_id=2"
        Then the response code is 200
        And the response is an object with id=1,deployment_id=1,tier_id=2,status="pending",environment_id=2,package_id=1
        And there is a tier deployment with id=1,deployment_id=1,app_id=2,status="pending",environment_id=2,package_id=1

    @rest
    Scenario Outline: POST host deployment to unauthorized environment
        Given there is an environment with name="dev"
        And there is an environment with name="staging"
        And there is an environment with name="prod"
        And there is a project with name="proj1"
        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | pending   |
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are applications:
            | name  |
            | app1  |
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
        And the tier "tier1" is associated with the application "app1" for the project "proj1"
        And there are hosts:
            | name  | app_id    | env   |
            | host1 | 2         | prod  |
        And I have a cookie with user permissions and environments=<envs>
        When I query POST "/host_deployments?deployment_id=1&host_id=1&package_id=1"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                                   |
            | header    | cookie    | Insufficient authorization. This cookie only has permissions for the following environment IDs: [<env_list>]. |

        Examples:
            | envs  | env_list  |
            | 1     | 1         |
            | 2     | 2         |
            | 1+2   | 1, 2      |

    @rest
    Scenario Outline: POST host deployment to authorized environment
        Given there is an environment with name="dev"
        And there is an environment with name="staging"
        And there is an environment with name="prod"
        And there is a project with name="proj1"
        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | pending   |
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are applications:
            | name  |
            | app1  |
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
        And the tier "tier1" is associated with the application "app1" for the project "proj1"
        And there are hosts:
            | name  | app_id    | env   |
            | host1 | 2         | dev   |
        And I have a cookie with user permissions and environments=<envs>
        When I query POST "/host_deployments?deployment_id=1&host_id=1&package_id=1"
        Then the response code is 201
        And the response is an object with id=1,deployment_id=1,host_id=1,package_id=1
        And there is a host deployment with id=1,deployment_id=1,host_id=1,package_id=1

        Examples:
            | envs  | env_list  |
            | 1     | 1         |
            | 1+2   | 1, 2      |

    @rest
    Scenario Outline: PUT host deployment to unauthorized environment
        Given there is an environment with name="dev"
        And there is an environment with name="staging"
        And there is an environment with name="prod"
        And there is a project with name="proj1"
        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | pending   |
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are applications:
            | name  |
            | app1  |
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
        And the tier "tier1" is associated with the application "app1" for the project "proj1"
        And there are hosts:
            | name  | app_id    | env   |
            | host1 | 2         | dev   |
            | host2 | 2         | prod  |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 1     | 1             | 1         | pending   | foo   | 1             |
        And I have a cookie with user permissions and environments=<envs>
        When I query PUT "/host_deployments/1?host_id=2"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                                   |
            | header    | cookie    | Insufficient authorization. This cookie only has permissions for the following environment IDs: [<env_list>]. |

        Examples:
            | envs  | env_list  |
            | 1     | 1         |
            | 2     | 2         |
            | 1+2   | 1, 2      |

    @rest
    Scenario: PUT host deployment to authorized environment
        Given there is an environment with name="dev"
        And there is an environment with name="staging"
        And there is an environment with name="prod"
        And there is a project with name="proj1"
        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | pending   |
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are applications:
            | name  |
            | app1  |
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
        And the tier "tier1" is associated with the application "app1" for the project "proj1"
        And there are hosts:
            | name  | app_id    | env       |
            | host1 | 2         | dev       |
            | host2 | 2         | staging   |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 1     | 1             | 1         | pending   | foo   | 1             |
        And I have a cookie with user permissions and environments=1+2
        When I query PUT "/host_deployments/1?host_id=2"
        Then the response code is 200
        And the response is an object with id=1,deployment_id=1,host_id=2,status="pending",user="foo",package_id=1
        And there is a host deployment with id=1,deployment_id=1,host_id=2,status="pending",user="foo",package_id=1

    @rest
    Scenario Outline: PUT deployment with host deployments in unauthorized environment
        Given there is an environment with name="dev"
        And there is an environment with name="staging"
        And there is an environment with name="prod"
        And there is a project with name="proj1"
        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | pending   |
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are applications:
            | name  |
            | app1  |
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
        And the tier "tier1" is associated with the application "app1" for the project "proj1"
        And there are hosts:
            | name  | app_id    | env   |
            | host1 | 2         | dev   |
            | host2 | 2         | prod  |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 1     | 1             | 2         | pending   | foo   | 1             |
        And I have a cookie with user permissions and environments=<envs>
        When I query PUT "/deployments/1?status=queued"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                                   |
            | header    | cookie    | Insufficient authorization. This cookie only has permissions for the following environment IDs: [<env_list>]. |

        Examples:
            | envs  | env_list  |
            | 1     | 1         |
            | 2     | 2         |
            | 1+2   | 1, 2      |

    @rest
    Scenario Outline: PUT deployment with host deployments in authorized environment
        Given there is an environment with name="dev"
        And there is an environment with name="staging"
        And there is an environment with name="prod"
        And there is a project with name="proj1"
        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | pending   |
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are applications:
            | name  |
            | app1  |
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
        And the tier "tier1" is associated with the application "app1" for the project "proj1"
        And there are hosts:
            | name  | app_id    | env   |
            | host1 | 2         | dev   |
            | host2 | 2         | prod  |
        And there are host deployments:
            | id    | deployment_id | host_id   | status    | user  | package_id    |
            | 1     | 1             | 1         | pending   | foo   | 1             |
        And I have a cookie with user permissions and environments=<envs>
        When I query PUT "/deployments/1?status=queued"
        Then the response code is 200
        And the response is an object with id=1,status="queued"
        And there is a deployment with id=1,status="queued"

        Examples:
            | envs  | env_list  |
            | 1     | 1         |
            | 1+2   | 1, 2      |

    @rest
    Scenario Outline: PUT deployment tier deployments in unauthorized environment
        Given there is an environment with name="dev"
        And there is an environment with name="staging"
        And there is an environment with name="prod"
        And there is a project with name="proj1"
        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | pending   |
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are applications:
            | name  |
            | app1  |
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
        And the tier "tier1" is associated with the application "app1" for the project "proj1"
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 1     | 1             | 2         | pending   | foo   | 3                 | 1             |
        And I have a cookie with user permissions and environments=<envs>
        When I query PUT "/deployments/1?status=queued"
        Then the response code is 403
        And the response contains errors:
            | location  | name      | description                                                                                                   |
            | header    | cookie    | Insufficient authorization. This cookie only has permissions for the following environment IDs: [<env_list>]. |

        Examples:
            | envs  | env_list  |
            | 1     | 1         |
            | 2     | 2         |
            | 1+2   | 1, 2      |

    @rest
    Scenario Outline: PUT deployment tier deployments in unauthorized environment
        Given there is an environment with name="dev"
        And there is an environment with name="staging"
        And there is an environment with name="prod"
        And there is a project with name="proj1"
        And there are deployments:
            | id    | user  | status    |
            | 1     | foo   | pending   |
        And there is a deploy target with name="tier1"
        And there is a deploy target with name="tier2"
        And there are applications:
            | name  |
            | app1  |
        And there are packages:
            | version   | revision  |
            | 1         | 1         |
        And the tier "tier1" is associated with the application "app1" for the project "proj1"
        And there are tier deployments:
            | id    | deployment_id | app_id    | status    | user  | environment_id    | package_id    |
            | 1     | 1             | 2         | pending   | foo   | 1                 | 1             |
        And I have a cookie with user permissions and environments=<envs>
        When I query PUT "/deployments/1?status=queued"
        Then the response code is 200
        And the response is an object with id=1,status="queued"
        And there is a deployment with id=1,status="queued"

        Examples:
            | envs  | env_list  |
            | 1     | 1         |
            | 1+2   | 1, 2      |
