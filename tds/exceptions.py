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

"""Custom exceptions for TagOps deployment program"""


class TDSException(Exception):
    """Exception specific to TDS."""

    pass


class AccessError(TDSException):
    """Exception for access violations (insufficient permissions)"""

    pass


class AlreadyExistsError(TDSException):
    """
    Exception for when attempting to create an object that already exists.
    """

    pass


class AssociatedTargetsError(TDSException):
    """
    Exception for when an attempt occurs to delete an application
    with associated targets
    """

    pass


class ConfigurationError(TDSException):
    """Exception for invalid or incomplete configuration files"""

    pass


# NOTE: This will no longer be needed once argparse is properly configured
class ExclusiveOptionError(TDSException):
    """Exception for when exclusive options are used together"""

    pass


class ExtCommandError(TDSException):
    """Custom exception for external command errors."""

    pass


class FailedConnectionError(TDSException):
    """Exception for when connections with Jenkins, etc. fail."""

    pass


class IllegalStateError(TDSException):
    """
    Exception raised when the program is in a state that it should not reach.
    For example, when validation is attempted on data that does not exist.
    """

    pass


class InvalidInputError(TDSException):
    """Exception for invalid input from user."""

    pass


class InvalidOperationError(TDSException):
    """Exception for when a user tries to perform an invalid operation."""

    pass


class InvalidRPMError(TDSException):
    """Exception for when an RPM is found to be broken or invalid."""

    pass


class JenkinsJobNotFoundError(TDSException):
    """Exception for when a Jenkins job is not found."""

    def __init__(self, object_type, job, version, jenkins_url):
        message = "{object_type} does not exist on {url}: {job}@{version}"\
            .format(
                object_type=object_type,
                url=jenkins_url,
                job=job,
                version=version,
            )

        super(JenkinsJobNotFoundError, self).__init__(message)


class JenkinsJobTransferError(TDSException):
    """Exception for when a Jenkins job is not transferred correctly."""

    def __init__(self, object_type, job, version, jenkins_url):
        message = "{object_type} was not transferred correctly from {url}: "\
                  "{job}@{version}"\
            .format(
                object_type=object_type,
                url=jenkins_url,
                job=job,
                version=version,
            )

        super(JenkinsJobTransferError, self).__init__(message)


class MultipleResultsError(TDSException):
    """Exception for when multiple results are returned and a single
       result is expected
    """

    pass


class NotFoundError(TDSException):
    """Exception for when an item is not found or does not exist."""

    def __init__(self, object_type, objects, sing_end='', plu_end='s'):
        """Create message given object_type and objects."""
        if not isinstance(objects, str):
            try:
                objects = list(objects)
            except TypeError:
                objects = [objects]
        message = "{object_type}{p1} do{p2} not exist: {objects}".format(
            object_type=object_type,
            p1=sing_end if len(objects) == 1 else plu_end,
            p2='es' if len(objects) == 1 else '',
            objects=', '.join(objects)
        )
        super(NotFoundError, self).__init__(message)


class ProgrammingError(TDSException):
    """
    Exception for when the application has been programmed incorrectly by the
    developer(s). Usually, this occurs when bindings between layers of TDS are
    broken or misused, such as misuse of decorators or constructors.
    """

    pass


class RunProcessError(TDSException):
    """
    Extends subprocess's CalledProcessError exception to include additional
    information used by TDS (stdout, stderr, duration - output is unused).
    """

    def __init__(self, returncode, cmd, output=None, stdout=None, stderr=None,
                 duration=None):
        self.returncode = returncode
        self.cmd = cmd
        self.output = output
        self.stdout = stdout
        self.stderr = stderr
        self.duration = duration

    def __str__(self):
        return "Command '%s' returned non-zero exit status %d" % \
               (self.cmd, self.returncode)


class WrongEnvironmentError(TDSException):
    """Exception for command attempts in incorrect environment"""

    pass


class WrongProjectTypeError(TDSException):
    """Exception for command attempts with incorrect project type"""

    pass
