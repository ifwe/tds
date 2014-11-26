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
# test multiple copies and failures -- status shoudl be failed and file removed on final failure
# umask is set correctly when running make (for yum repo)
# make is run properly (package should be added successfully)
# make fails once (package should be added successfully)
# make fails twice (package status should be set to failed, file removed)
# files are all removed from processing
# after failure, make sure can still add

# note: test with single and multiple packages
