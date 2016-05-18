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

Feature: package add application version [-f|--force]
    As a user
    I want to add a specific version of a package
    So I can deploy that version of that package to targets

    Background:
        Given I have "dev" permissions
        And there is an environment with name="dev"
        And I am in the "dev" environment

    Scenario: too few arguments
        When I run "package add myapp --detach"
        Then the output has "usage:"

    Scenario: too many arguments
        When I run "package add myapp vers foo --detach"
        Then the output has "usage:"

    Scenario: add a package to an application that doesn't exist
        When I run "package add myapp 123 --detach"
        Then the output is "Application does not exist: myapp"

    Scenario: attempt to add package when jenkins is not accessible
        Given there is an application with name="myapp"
        When I run "package add myapp 123 --detach"
        Then the output has "Unable to contact Jenkins server"
        And there is no package with name="myapp",version="123"

    @jenkins_server
    Scenario: add a package to an application with a job name that doesn't exist
        Given there is an application with name="myapp"
        When I run "package add myapp 123 --detach"
        Then the output has "Job does not exist on http://localhost"
        And the output has "job@123"
        And there is no package with name="myapp",version="123"

    @jenkins_server
    Scenario: add a package to an application with a version that doesn't exist
        Given there is an application with name="myapp"
        And there is a jenkins job with name="job"
        When I run "package add myapp 123 --detach"
        Then the output has "Build does not exist on http://localhost"
        And the output has "job@123"
        And there is no package with name="myapp",version="123"

    @jenkins_server
    Scenario: with --job flag indicating a non-existent job
        Given there is an application with name="myapp"
        And there is a jenkins job with name="job"
        And the job has a build with number="123"
        When I run "package add --job another_job myapp 123 --detach"
        Then the output has "Job does not exist on http://localhost"
        And the output has "job@123"
        And there is no package with name="myapp",version=123

    @jenkins_server
    Scenario: add a package that has previously failed to an application
        Given there is an application with name="myapp"
        And there is a jenkins job with name="job"
        And the job has a build with number="123"
        And there is a package with name="myapp",version="123",status="failed"
        When I run "package add myapp 123 --detach"
        Then the output has "Package already exists with failed status. Changing status to pending for daemon to attempt re-adding..."
        And the output has "Package ready for repo updater daemon. Disconnecting now."
        And there is a package with name="myapp",version="123",status="pending",job="job"

    @jenkins_server
    Scenario: add a package to an application
        Given there is an application with name="myapp"
        And there is a jenkins job with name="job"
        And the job has a build with number="123"
        When I run "package add myapp 123 --detach"
        Then the output has "Package ready for repo updater daemon. Disconnecting now."
        And there is a package with name="myapp",version="123",status="pending",job="job"

    @jenkins_server
    Scenario: with explicit --job flag
        Given there is an application with name="myapp"
        And there is a jenkins job with name="another_job"
        And the job has a build with number="123"
        When I run "package add --job another_job myapp 123 --detach"
        Then the output has "Package ready for repo updater daemon. Disconnecting now."
        And there is a package with name="myapp",version="123",status="pending",job="another_job"

    @jenkins_server
    Scenario: override default job with explicit --job flag
        Given there is an application with name="myapp"
        And there is a jenkins job with name="job"
        And there is a jenkins job with name="another_job"
        And the job has a build with number="123"
        When I run "package add --job another_job myapp 123 --detach"
        Then the output has "Package ready for repo updater daemon. Disconnecting now."
        And there is a package with name="myapp",version="123",status="pending",job="another_job"

    @jenkins_server
    Scenario: add a package to an application again
        Given there is an application with name="myapp"
        And there is a package with version="123"
        And there is a jenkins job with name="job"
        And the job has a build with number="123"
        When I run "package add myapp 123 --detach"
        Then the output has "Package already exists with status completed."

    @jenkins_server
    Scenario: add a package to an application again with --force
        Given there is an application with name="myapp"
        And there is a package with version="123"
        And there is a jenkins job with name="job"
        And the job has a build with number="123"
        When I run "package add myapp 123 --detach --force"
        Then the output has "Package was previously completed. Changing status to pending again for daemon to attempt re-adding..."
        And there is a package with name="myapp",version="123",status="pending",job="job"

    @jenkins_server
    Scenario: add a package to an application again with the previous package in processing state
        Given there is an application with name="myapp"
        And there is a package with version="123",status="processing"
        And there is a jenkins job with name="job"
        And the job has a build with number="123"
        When I run "package add myapp 123 --detach --force"
        Then the output has "Package already being processed by daemon. Added"

    # TODO: There are probably more failure tests that can be written here!
    # e.g. test for already-exists package in various states: completed, pending, processing, removed, failed

    # Scenario: after failure, make sure can still add
