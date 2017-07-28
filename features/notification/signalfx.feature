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

Feature: Signalfx notifications
    As a developer
    I want to send Signalfx notifications
    So that I can better collaborate with other developers

    Background:
        Given I have "stage" permissions
        And there are environments
            | name   |
            | dev    |
            | stage  |
        And I am in the "stage" environment
        And there is a project with name="proj"
        And there is an application with name="myapp"
        And there is a deploy target with name="the-apptype"
        And there is a package with version="123"
        And the package is deployed on the deploy targets in the "dev" env
        And the package has been validated in the "development" environment
        And there are hosts:
            | name          | env   |
            | dprojhost01   | dev   |
            | dprojhost02   | dev   |
            | sprojhost01   | stage |
            | sprojhost02   | stage |
        And the deploy target is a part of the project-application pair
        And the hosts are associated with the deploy target

    @signalfx_server
    Scenario: deploying to multiple hosts of different apptypes
        Given there is a deploy target with name="other-apptype"
        And there are hosts:
            | name       | env    |
            | dother01   | dev    |
            | dother02   | dev    |
            | sother01   | stage  |
            | sother02   | stage  |
        And the hosts are associated with the deploy target
        And the deploy target is a part of the project-application pair
        And there is a package with version="124"
        And the package is deployed on the deploy targets in the "dev" env
        And the package has been validated in the "development" environment
        And signalfx notifications are enabled
        When I run "deploy promote myapp 124 --hosts sprojhost01 --detach"
        And I run "deploy promote myapp 124 --hosts sprojhost02 --detach"
        And I run "deploy promote myapp 124 --hosts sother01 --detach"
        Then there was a signalfx notification with deploy_type="promote",release_version="124",artifact_name="myapp",node="sprojhost01",env="stage"
        And there are 3 signalfx notifications

    @signalfx_server
    Scenario: deploying to all apptypes
        Given there is a package with version="124"
        And the package is deployed on the deploy targets in the "dev" env
        And the package has been validated in the "development" environment
        And signalfx notifications are enabled
        When I run "deploy promote myapp 124 --all-apptypes --detach"
        Then there was a signalfx notification with deploy_type="promote",release_version="124",artifact_name="myapp",application="the-apptype",env="stage"
        And there are 1 signalfx notifications

    @signalfx_server
    Scenario: deploying to specific apptypes
        Given there is a package with version="124"
        And the package is deployed on the deploy targets in the "dev" env
        And the package has been validated in the "development" environment
        And signalfx notifications are enabled
        When I run "deploy promote myapp 124 --apptypes the-apptype --detach"
        Then there was a signalfx notification with deploy_type="promote",release_version="124",artifact_name="myapp",application="the-apptype",env="stage"
        And there are 1 signalfx notifications

    @signalfx_server
    Scenario: fix on all apptypes
        Given there is a deploy target with name="another-apptype"
        And there is a host with name="anotherhost01"
        And the host is associated with the deploy target
        And the deploy target is a part of the project-application pair
        And the package is deployed on the deploy target
        And the package failed to deploy on the host with name="anotherhost01"
        And signalfx notifications are enabled
        When I run "deploy fix myapp --all-apptypes --detach"
        Then there was a signalfx notification with deploy_type="fix",release_version"123",artifact_name="myapp",application="another-apptype",env="stage"
        And there are 1 signalfx notifications

    @signalfx_server
    Scenario: fix on specific apptypes
        Given there is a deploy target with name="another-apptype"
        And there is a host with name="anotherhost01"
        And the host is associated with the deploy target
        And the deploy target is a part of the project-application pair
        And the package is deployed on the deploy target
        And the package failed to deploy on the host with name="anotherhost01"
        And signalfx notifications are enabled
        When I run "deploy fix myapp --apptypes another-apptype --detach"
        Then there was a signalfx notification with deploy_type="fix",release_version="123",artifact_name="myapp",application="another-apptype",env="stage"
        And there are 1 signalfx notifications

    @signalfx_server
    Scenario: fix on specific host
        Given there is a deploy target with name="another-apptype"
        And there is a host with name="anotherhost01"
        And the host is associated with the deploy target
        And the deploy target is a part of the project-application pair
        And the package is deployed on the deploy target
        And the package failed to deploy on the host with name="anotherhost01"
        And signalfx notifications are enabled
        When I run "deploy fix myapp --hosts anotherhost01 --detach"
        Then there was a signalfx notification with deploy_type="fix",release_version="123",artifact_name="myapp",node="anotherhost01",env="stage"
        And there are 1 signalfx notifications

    @signalfx_server
    Scenario: rollback version on apptype
        Given the package is deployed on the deploy target
        And the package has been validated

        And I wait 1 seconds
        And there is a package with version="121"
        And the package is deployed on the deploy target
        And the package has been validated

        And I wait 1 seconds
        And there is a package with version="122"
        And the package is deployed on the deploy target
        And the package has been invalidated

        And signalfx notifications are enabled

        When I run "deploy rollback myapp --apptype the-apptype --detach"
        Then there was a signalfx notification with deploy_type="rollback",release_version="121",artifact_name="myapp",application="the-apptype",env="stage"
        And there are 1 signalfx notifications

    @signalfx_server
    Scenario: rollback version on all apptypes
        Given the package is deployed on the deploy target
        And the package has been validated

        And I wait 1 seconds
        And there is a package with version="121"
        And the package is deployed on the deploy target
        And the package has been validated

        And I wait 1 seconds
        And there is a package with version="122"
        And the package is deployed on the deploy target
        And the package has been invalidated

        And signalfx notifications are enabled

        When I run "deploy rollback myapp --all-apptypes --detach"
        Then there was a signalfx notification with deploy_type="rollback",release_version="121",artifact_name="myapp",application="the-apptype",env="stage"
        And there are 1 signalfx notifications

    @signalfx_server
    Scenario: rollback version on specific host
        Given the package is deployed on the deploy target
        And the package has been validated

        And I wait 1 seconds
        And there is a package with version="124"
        And the package is deployed on the deploy target
        And the package has been validated

        And I wait 1 seconds
        And there is a package with version="125"
        And the package is deployed on the deploy target
        And the package has been invalidated

        And signalfx notifications are enabled

        When I run "deploy rollback myapp --hosts sprojhost01 --detach"
        Then there was a signalfx notification with deploy_type="rollback",release_version="124",artifact_name="myapp",node="sprojhost01",env="stage"
        And there are 1 signalfx notifications

    @signalfx_server
    Scenario: signalfx server failure
        Given the package is deployed on the deploy target
        And the package has been validated

        And I wait 1 seconds
        And there is a package with version="200"
        And the package is deployed on the deploy target
        And the package has been validated

        And I wait 1 seconds
        And there is a package with version="201"
        And the package is deployed on the deploy target
        And the package has been invalidated

        And signalfx notifications are enabled

        When I run "deploy rollback myapp --hosts sprojhost01 --detach"
        Then there is a signalfx failure
        And the output has "Deployment successful, but failed to send Signalfx notification. Got status code 403."

    @signalfx_server
    Scenario: no signalfx response
        Given there is a package with version="500"
        And the package is deployed on the deploy targets in the "dev" env
        And the package has been validated in the "development" environment

        And signalfx notifications are enabled

        When I run "deploy promote myapp 500 --all-apptypes --detach"
        Then the output has "Deployment successful, but failed to send Signalfx notification. Got exception: "
