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

Feature: deploy daemon
    As a deploy daemon
    I want to deploy queued deployments
    So that software can be deployed where needed

    Background:
        Given there are environments
            | name  |
            | dev   |
            | stage |
        And there is a project with name="proj"
        And there is an application with name="myapp"
        And there is a deploy target with name="tier1"
        And I am in the "dev" environment
        And there are hosts:
            | name  | env   | app_id    |
            | host1 | dev   | 2         |
        And there are packages:
            | version   | revision  |
            | 121       | 1         |
        And there are deployments:
            | id    | user  | status        |
            | 1     | foo   | complete      |
            | 2     | foo   | failed        |
            | 3     | foo   | inprogress    |
            | 4     | foo   | pending       |
            | 5     | foo   | canceled      |
        And there are tier deployments:
            | id    | deployment_id | status        | user  | app_id    | package_id    | environment_id    |
            | 1     | 1             | validated     | foo   | 2         | 1             | 1                 |
            | 2     | 2             | incomplete    | foo   | 2         | 1             | 1                 |
            | 3     | 3             | inprogress    | foo   | 2         | 1             | 1                 |
            | 4     | 4             | pending       | foo   | 2         | 1             | 1                 |
            | 5     | 5             | pending       | foo   | 2         | 1             | 1                 |
        And there are host deployments:
            | id    | deployment_id | status        | user  | host_id   | package_id    |
            | 1     | 1             | ok            | foo   | 1         | 1             |
            | 2     | 2             | failed        | foo   | 1         | 1             |
            | 3     | 3             | inprogress    | foo   | 1         | 1             |
            | 4     | 4             | pending       | foo   | 1         | 1             |
            | 5     | 5             | pending       | foo   | 1         | 1             |

    Scenario Outline: run daemon with no queued deployments
        Given the deploy strategy is "<strategy>"
        When I run "deploy_daemon"
        Then there were no deployments run

        Examples:
            | strategy  |
            | salt      |
            | mco       |

    Scenario Outline: run daemon with a deployment queued with a tier deployment in a different environment
        Given there are deployments:
            | id    | user  | status    |
            | 6     | foo   | queued    |
        And there are tier deployments:
            | id    | deployment_id | status    | user  | app_id    | package_id    | environment_id    |
            | 6     | 6             | pending   | foo   | 2         | 1             | 2                 |
        And the deploy strategy is "<strategy>"
        When I run "deploy_daemon"
        Then there were no deployments run
        And there is a deployment with id=6,status="queued"
        And there is a tier deployment with id=6,deployment_id=6,status="pending"

        Examples:
            | strategy  |
            | salt      |
            | mco       |

    Scenario Outline: run daemon with a deployment queued with a tier deployment in a different environment
        Given there are deployments:
            | id    | user  | status    |
            | 6     | foo   | queued    |
        And there are hosts:
            | name  | env   | app_id    |
            | host2 | stage | 2         |
        And there are host deployments:
            | id    | deployment_id | status    | user  | host_id   | package_id    |
            | 6     | 6             | pending   | foo   | 2         | 1             |
        And the deploy strategy is "<strategy>"
        When I run "deploy_daemon"
        Then there were no deployments run
        And there is a deployment with id=6,status="queued"
        And there is a host deployment with id=6,deployment_id=6,status="pending"

        Examples:
            | strategy  |
            | salt      |
            | mco       |

    Scenario Outline: run daemon with a deployment queued with a tier deployment in a different environment
        Given there are deployments:
            | id    | user  | status    |
            | 6     | foo   | queued    |
        And there are hosts:
            | name  | env   | app_id    |
            | host2 | stage | 2         |
        And there are tier deployments:
            | id    | deployment_id | status    | user  | app_id    | package_id    | environment_id    |
            | 6     | 6             | pending   | foo   | 2         | 1             | 2                 |
        And there are host deployments:
            | id    | deployment_id | status    | user  | host_id   | package_id    |
            | 6     | 6             | pending   | foo   | 2         | 1             |
        And the deploy strategy is "<strategy>"
        When I run "deploy_daemon"
        Then there were no deployments run
        And there is a deployment with id=6,status="queued"
        And there is a tier deployment with id=6,deployment_id=6,status="pending"
        And there is a host deployment with id=6,deployment_id=6,status="pending"

        Examples:
            | strategy  |
            | salt      |
            | mco       |

    Scenario Outline: run daemon with a tier deployment with no hosts
        Given there is a deploy target with name="tier2"
        And there are deployments:
            | id    | user  | status    |
            | 6     | foo   | queued    |
        And there are tier deployments:
            | id    | deployment_id | status    | user  | app_id    | package_id    | environment_id    |
            | 6     | 6             | <tier_st> | foo   | 3         | 1             | 1                 |
        And the deploy strategy is "<strategy>"
        When I run "deploy_daemon"
        Then there is a deployment with id=6,status="complete"
        And the deployment with id=6 has duration greater than 0
        And there is a tier deployment with id=6,deployment_id=6,status="complete"
        And the tier deployment with id=6 has duration greater than 0

        Examples:
            | strategy  | tier_st       |
            | salt      | pending       |
            | salt      | incomplete    |
            | mco       | pending       |
            | mco       | incomplete    |

    Scenario Outline: run daemon with a tier deployment with hosts
        Given there are deployments:
            | id    | user  | status    |
            | 6     | foo   | queued    |
        And there are tier deployments:
            | id    | deployment_id | status    | user  | app_id    | package_id    | environment_id    |
            | 6     | 6             | <tier_st> | foo   | 2         | 1             | 1                 |
        And there are host deployments:
            | id    | deployment_id | status    | user  | host_id   | package_id    |
            | 6     | 6             | <host_st> | foo   | 1         | 1             |
        And the deploy strategy is "<strategy>"
        When I run "deploy_daemon"
        Then there is a deployment with id=6,status="complete"
        And the deployment with id=6 has duration greater than 0
        And there is a tier deployment with id=6,deployment_id=6,status="complete"
        And the tier deployment with id=6 has duration greater than 0
        And there is a host deployment with id=6,deployment_id=6,status="ok"
        And the host deployment with id=6 has duration greater than 0
        And package "myapp" version "121" was deployed to the deploy target with name="tier1"

        Examples:
            | strategy  | tier_st       | host_st   |
            | salt      | pending       | pending   |
            | salt      | incomplete    | failed    |
            | salt      | incomplete    | pending   |
            | mco       | pending       | pending   |
            | mco       | incomplete    | failed    |
            | mco       | incomplete    | pending   |

    Scenario Outline: run daemon with multiple tier & host deployments
        Given there is a deploy target with name="tier2"
        And there are hosts:
            | name  | env   | app_id    |
            | host2 | dev   | 3         |
            | host3 | dev   | 3         |
        And there are deployments:
            | id    | user  | status    |
            | 6     | foo   | queued    |
        And there are tier deployments:
            | id    | deployment_id | status    | user  | app_id    | package_id    | environment_id    |
            | 6     | 6             | pending   | foo   | 2         | 1             | 1                 |
            | 7     | 6             | <tier_st> | foo   | 3         | 1             | 1                 |
        And there are host deployments:
            | id    | deployment_id | status    | user  | host_id   | package_id    |
            | 6     | 6             | pending   | foo   | 1         | 1             |
            | 7     | 6             | <host_st> | foo   | 2         | 1             |
            | 8     | 6             | ok        | foo   | 3         | 1             |
        And the deploy strategy is "<strategy>"
        When I run "deploy_daemon"
        Then there is a deployment with id=6,status="complete"
        And the deployment with id=6 has duration greater than 0
        And there is a tier deployment with id=6,deployment_id=6,status="complete"
        And the tier deployment with id=6 has duration greater than 0
        And there is a tier deployment with id=7,deployment_id=6,status="complete"
        And the tier deployment with id=7 has duration greater than 0
        And there is a host deployment with id=6,deployment_id=6,status="ok"
        And the host deployment with id=6 has duration greater than 0
        And there is a host deployment with id=7,deployment_id=6,status="ok"
        And the host deployment with id=7 has duration greater than 0
        And there is a host deployment with id=8,deployment_id=6,status="ok",duration=0
        And package "myapp" version "121" was deployed to the deploy target with name="tier1"
        And package "myapp" version "121" was deployed to host "host2"
        And package "myapp" version "121" was not deployed to host "host3"

        Examples:
            | strategy  | tier_st       | host_st   |
            | salt      | pending       | pending   |
            | salt      | incomplete    | failed    |
            | salt      | incomplete    | pending   |
            | mco       | pending       | pending   |
            | mco       | incomplete    | failed    |
            | mco       | incomplete    | pending   |

    Scenario Outline: run daemon with a tier & host deployment each, with one host missing
        Given there is a deploy target with name="tier2"
        And there are hosts:
            | name  | env   | app_id    |
            | host2 | dev   | 3         |
            | host3 | dev   | 3         |
        And there are deployments:
            | id    | user  | status    |
            | 6     | foo   | queued    |
        And there are tier deployments:
            | id    | deployment_id | status    | user  | app_id    | package_id    | environment_id    |
            | 6     | 6             | pending   | foo   | 2         | 1             | 1                 |
            | 7     | 6             | <tier_st> | foo   | 3         | 1             | 1                 |
        And there are host deployments:
            | id    | deployment_id | status    | user  | host_id   | package_id    |
            | 6     | 6             | pending   | foo   | 1         | 1             |
            | 7     | 6             | <host_st> | foo   | 2         | 1             |
        And the deploy strategy is "<strategy>"
        When I run "deploy_daemon"
        Then there is a deployment with id=6,status="complete"
        And the deployment with id=6 has duration greater than 0
        And there is a tier deployment with id=6,deployment_id=6,status="complete"
        And the tier deployment with id=6 has duration greater than 0
        And there is a tier deployment with id=7,deployment_id=6,status="complete"
        And the tier deployment with id=7 has duration greater than 0
        And there is a host deployment with id=6,deployment_id=6,status="ok"
        And the host deployment with id=6 has duration greater than 0
        And there is a host deployment with id=7,deployment_id=6,status="ok"
        And the host deployment with id=7 has duration greater than 0
        And package "myapp" version "121" was deployed to the deploy target with name="tier1"
        And package "myapp" version "121" was deployed to host "host2"
        And package "myapp" version "121" was not deployed to host "host3"

        Examples:
            | strategy  | tier_st       | host_st   |
            | salt      | pending       | pending   |
            | salt      | incomplete    | failed    |
            | salt      | incomplete    | pending   |
            | mco       | pending       | pending   |
            | mco       | incomplete    | failed    |
            | mco       | incomplete    | pending   |

    Scenario Outline: cancel tier and host deployment partway through
        Given there is a deploy target with name="tier2"
        And there are hosts:
            | name  | env   | app_id    |
            | host2 | dev   | 2         |
            | host3 | dev   | 3         |
        And there are deployments:
            | id    | user  | status    | delay |
            | 6     | foo   | queued    | 20    |
        And there are tier deployments:
            | id    | deployment_id | status    | user  | app_id    | package_id    | environment_id    |
            | 6     | 6             | pending   | foo   | 2         | 1             | 1                 |
            | 7     | 6             | <tier_st> | foo   | 3         | 1             | 1                 |
        And there are host deployments:
            | id    | deployment_id | status    | user  | host_id   | package_id    |
            | 6     | 6             | pending   | foo   | 1         | 1             |
            | 7     | 6             | <host_st> | foo   | 2         | 1             |
            | 8     | 6             | ok        | foo   | 3         | 1             |
        And the deploy strategy is "<strategy>"
        When I start to run "deploy_daemon"
        And I wait 10 seconds
        And the status of the deployment with id=6 changes to "canceled"
        And I wait 20 seconds
        And the command finishes
        Then there is a deployment with id=6,status="stopped"
        And the deployment with id=6 has duration greater than 20
        And there is a tier deployment with id=6,deployment_id=6,status="incomplete"
        And the tier deployment with id=6 has duration greater than 20
        And there is a tier deployment with id=7,deployment_id=6,status="<tier_st>",duration=0
        And there is a host deployment with id=6,deployment_id=6,status="ok"
        And the host deployment with id=6 has duration greater than 0
        And there is a host deployment with id=7,deployment_id=6,status="<host_st>",duration=0
        And there is a host deployment with id=8,deployment_id=6,status="ok",duration=0
        And package "myapp" version "121" was deployed to host "host1"
        And package "myapp" version "121" was not deployed to host "host2"
        And package "myapp" version "121" was not deployed to host "host3"

        Examples:
            | strategy  | tier_st       | host_st   |
            | salt      | pending       | pending   |
            | salt      | incomplete    | failed    |
            | salt      | incomplete    | pending   |
            | mco       | pending       | pending   |
            | mco       | incomplete    | failed    |
            | mco       | incomplete    | pending   |

    Scenario Outline: cancel host deployments partway through
        Given there is a deploy target with name="tier2"
        And there are hosts:
            | name  | env   | app_id    |
            | host2 | dev   | 2         |
            | host3 | dev   | 3         |
        And there are deployments:
            | id    | user  | status    | delay |
            | 6     | foo   | queued    | 20    |
        And there are host deployments:
            | id    | deployment_id | status    | user  | host_id   | package_id    |
            | 6     | 6             | pending   | foo   | 1         | 1             |
            | 7     | 6             | <host_st> | foo   | 2         | 1             |
            | 8     | 6             | ok        | foo   | 3         | 1             |
        And the deploy strategy is "<strategy>"
        When I start to run "deploy_daemon"
        And I wait 10 seconds
        And the status of the deployment with id=6 changes to "canceled"
        And I wait 20 seconds
        And the command finishes
        Then there is a deployment with id=6,status="stopped"
        And the deployment with id=6 has duration greater than 20
        And there is a host deployment with id=6,deployment_id=6,status="ok"
        And the host deployment with id=6 has duration greater than 0
        And there is a host deployment with id=7,deployment_id=6,status="<host_st>",duration=0
        And there is a host deployment with id=8,deployment_id=6,status="ok",duration=0
        And package "myapp" version "121" was deployed to host "host1"
        And package "myapp" version "121" was not deployed to host "host2"
        And package "myapp" version "121" was not deployed to host "host3"

        Examples:
            | strategy  | host_st   |
            | salt      | pending   |
            | salt      | failed    |
            | mco       | pending   |
            | mco       | failed    |
