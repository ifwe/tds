# TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO
# adding a package
# adding an invalid package (broken rpm) -- make sure it gets removed
# interrupted while adding a package
# file can't be removed
# test config loading and failure modes
# emails for invalid RPMs
# fail to send email for invalid RPMs
# package entry does not exist
# file is correctly moved
# failure to move file (file should be removed and package status failed)
# package is added correctly and is set to processing
# test race condition with package entry being invalidated in various ways
# test race condition with file being removed before repo update
# test multiple copies and failures -- status should be failed and file removed on final failure
# umask is set correctly when running make (for yum repo)
# make is run properly (package should be added successfully)
# make fails once (package should be added successfully)
# make fails twice (package status should be set to failed, file removed)
# files are all removed from processing
# after failure, make sure can still add

# note: test with single and multiple packages

Feature: YUM repo updater
    As a developer
    I want to have the YUM repo updated and handling files correctly
    So that I can be certain that the packages I add are actually added

    Background:
        Given there is an application with name="myapp"
        And there is a package with version="123",status="pending"

    Scenario: adding a package
        Given there is an RPM package with name="myapp",version="123",revision="1",arch="noarch"
        And make will return 0
        When I run "daemon"
        Then the "incoming" directory is empty
        And the "processing" directory is empty
        And the package status is "completed"

    # TODO: TDS-45.  After that's done, remove this test; it will no longer be valid.
    @email_server
    Scenario: adding an invalid package (broken rpm)
        Given a file with name "pkg.rpm" is in the "incoming" directory
        And email notification is enabled
        When I run "daemon"
        Then an email is sent with repo update info with sender="siteops",receiver="eng+tds@tagged.com"
        And an email is sent with repo update contents containing "[TDS] Invalid RPM file "pkg.rpm""
        And an email is sent with repo update contents containing "The RPM file "pkg.rpm" is invalid, the builder of it should check the build process"
        # And the package status is "failed"

    Scenario: make fails once (package should be added successfully)
        Given there is an RPM package with name="myapp",version="123",revision="1",arch="noarch"
        And make will return 2,0
        When I run "daemon"
        Then the "incoming" directory is empty
        And the "processing" directory is empty
        And the package status is "completed"
        And the update repo log file has "ERROR yum database update failed, retrying:"

    Scenario: make fails twice (package status should be set to failed, file removed)
        Given there is an RPM package with name="myapp",version="123",revision="1",arch="noarch"
        And make will return 2,2
        When I run "daemon"
        Then the "incoming" directory is empty
        And the "processing" directory is empty
        And the package status is "failed"
        And the update repo log file has "ERROR yum database update failed, aborting:"

    # Scenario: interrupt while adding a package

    # Scenario: file can't be removed

    # Scenario: test config loading and failure modes

    @email_server
    Scenario: fail to send email for invalid RPMs
        Given a file with name "pkg.rpm" is in the "incoming" directory
        And email notification is enabled
        And the email server is broken
        When I run "daemon"
        Then the update repo log file has "ERROR Email send failed:"

    # Scenario: package entry does not exist

    # Scenario: failure to move file

    # Scenario: race condition with package entry being invalidated in various ways

    # Scenario: race condition with file being removed before repo update

    # Scenario: multiple copies and failures -- status should be failed and file removed on final failure

    # Scenario: umask is set correctly when running make (for yum repo)
