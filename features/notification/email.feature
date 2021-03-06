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

Feature: email notifications
    As an administrator
    I want to enable email notifications
    So that developers are notified via email about deployments from TDS

    Background:
        Given I have "dev" permissions
        And there is an environment with name="dev"
        And I am in the "dev" environment
        And email notification is enabled
        And there is a project with name="proj"
        And there is an application with name="myapp"
        And there is a deploy target with name="the-apptype"
        And there is a package with version="123"
        And there are hosts:
            | name          | env   |
            | dprojhost01   | dev   |
            | dprojhost02   | dev   |
        And the deploy target is a part of the project-application pair
        And the hosts are associated with the deploy target
        And there is a deploy target with name="another-apptype"
        And there is a host with name="danotherhost01",env="dev"
        And the host is associated with the deploy target
        And there is a host with name="danotherhost02",env="dev"
        And the host is associated with the deploy target
        And the deploy target is a part of the project-application pair

    @email_server
    Scenario: deployment of single apptype occurs with working mail notification
        When I run "deploy promote myapp 123 --apptypes the-apptype --detach"
        Then an email is sent with the relevant information for deptype="promote",apptypes="the-apptype"

    @email_server
    Scenario: deployment of all apptypes occurs with working mail notification
        When I run "deploy promote myapp 123 --all-apptypes --detach"
        Then an email is sent with the relevant information for deptype="promote",apptypes="another-apptype:the-apptype"

    @email_server
    Scenario: deployment of a host(s) occurs with working mail notification
        When I run "deploy promote myapp 123 --hosts dprojhost01 danotherhost01 --detach"
        Then an email is sent with the relevant information for deptype="promote",hosts="danotherhost01:dprojhost01"

    @email_server
    Scenario: fix of single apptype occurs with working mail notification
        Given the package is deployed on the deploy targets in the "dev" env
        And the package failed to deploy on the host with name="dprojhost02"
        When I run "deploy fix myapp --apptypes the-apptype --detach"
        Then an email is sent with the relevant information for deptype="fix",apptypes="the-apptype"

    @email_server
    Scenario: fix of all apptypes occurs with working mail notification
        Given the package is deployed on the deploy targets in the "dev" env
        And the package failed to deploy on the host with name="dprojhost02"
        When I run "deploy fix myapp --all-apptypes --detach"
        Then an email is sent with the relevant information for deptype="fix",apptypes="another-apptype:the-apptype"

    @email_server
    Scenario: fix of a host(s) occurs with working mail notification
        Given the package is deployed on the deploy targets in the "dev" env
        And the package failed to deploy on the host with name="dprojhost02"
        When I run "deploy fix myapp --hosts dprojhost02 --detach"
        Then an email is sent with the relevant information for deptype="fix",hosts="dprojhost02"

    @email_server
    Scenario: rollback of single apptype occurs with working mail notification
        Given the package is deployed on the deploy targets
        And the package has been validated
        And I wait 1 seconds
        And there is a package with version="124"
        And the package is deployed on the deploy targets
        And the package has been validated
        When I run "deploy rollback myapp --apptypes the-apptype --detach"
        Then an email is sent with the relevant information for deptype="rollback",apptypes="the-apptype"

    @email_server
    Scenario: rollback of all apptypes occurs with working mail notification
        Given the package is deployed on the deploy targets
        And the package has been validated
        And I wait 1 seconds
        And there is a package with version="124"
        And the package is deployed on the deploy targets
        And the package has been validated
        When I run "deploy rollback myapp --all-apptypes --detach"
        Then an email is sent with the relevant information for deptype="rollback",apptypes="another-apptype:the-apptype"

    @email_server
    Scenario: rollback of a host(s) occurs with a working mail notification
        Given the package is deployed on the deploy targets
        And the package has been validated
        And I wait 1 seconds
        And there is a package with version="124"
        And the package is deployed on the deploy targets
        When I run "deploy rollback myapp --hosts dprojhost01 danotherhost01 --detach"
        Then an email is sent with the relevant information for deptype="rollback",hosts="danotherhost01:dprojhost01"

    @email_server
    Scenario: email server fails while notification attempted
        Given the email server is broken
        When I run "deploy promote myapp 123 --apptypes the-apptype --detach"
        Then there is a failure message for the email send
