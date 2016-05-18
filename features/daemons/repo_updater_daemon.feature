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

Feature: YUM repo updater
    As a developer
    I want to have the YUM repo updated and handling files correctly
    So that I can be certain that the packages I add are actually added

    Background:
        Given there is an application with name="myapp"
        And there is a package with version="123",status="pending",revision="1"

    @jenkins_server @email_server
    Scenario: adding a package
        Given there is a jenkins job with name="job"
        And the job has a build with number="123"
        And make will return 0
        When I run "daemon"
        Then the "incoming" directory is empty
        And the "processing" directory is empty
        And there is a package with version="123",status="completed"

    @jenkins_server
    Scenario: make fails once (package should be added successfully)
        Given there is a jenkins job with name="job"
        And the job has a build with number="123"
        And make will return 2,0
        When I run "daemon"
        Then the "incoming" directory is empty
        And the "processing" directory is empty
        And there is a package with version="123",status="completed"
        And the update repo log file has "ERROR yum database update failed, retrying:"

    @jenkins_server
    Scenario: make fails twice (package status should be set to failed, file removed)
        Given there is a jenkins job with name="job"
        And the job has a build with number="123"
        And make will return 2,2
        When I run "daemon"
        Then the "incoming" directory is empty
        And the "processing" directory is empty
        And there is a package with version="123",status="failed"
        And the update repo log file has "ERROR yum database update failed, aborting:"

    @jenkins_server @email_server
    Scenario: fail to send email for invalid RPMs
        Given there is a jenkins job with name="job"
        And the job has a build with number="123" with malformed data
        And make will return 0
        And email notification is enabled
        And the email server is broken
        When I run "daemon"
        Then the "incoming" directory is empty
        And the "processing" directory is empty
        And there is a package with version="123",status="failed"
        And the update repo log file has "ERROR Email send failed:"

    @email_server
    Scenario: Jenkins unavailable
        When I run "daemon"
        Then the update repo log file has "ERROR Unable to contact Jenkins server at "

    @jenkins_server @email_server
    Scenario: artifact not on Jenkins
        Given there is a jenkins job with name="job"
        When I run "daemon"
        Then the update repo log file has "ERROR Failed to download RPM for package with id=1: Artifact does not exist on "

    # Scenario: file can't be removed

    # Scenario: test config loading and failure modes

    # Scenario: failure to move file

    # Scenario: race condition with package entry being invalidated in various ways

    # Scenario: race condition with file being removed before repo update

    # Scenario: multiple copies and failures -- status should be failed and file removed on final failure

    # Scenario: umask is set correctly when running make (for yum repo)

    # NOTE: test with single and multiple packages
