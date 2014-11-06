#
# Copyright (C) 2012 Tagged, Inc.
#
# All rights reserved


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


class ExtCommandError(TDSException):
    """Custom exception for external command errors."""

    pass


class FailedConnectionError(TDSException):
    """Exception for when connections with Jenkins, etc. fail."""

    pass


class InvalidInputError(TDSException):
    """Exception for invalid input from user."""

    pass


class InvalidOperationError(TDSException):
    """Exception for when a user tries to perform an invalid operation."""

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


class JenkinsJobNotFoundError(TDSException):
    """Exception for when a Jenkins jobs is not found."""

    def __init__(self, object_type, job, version, jenkins_url):
        message = "{object_type} does not exist on {url}: {job}@{version}"\
            .format(
                object_type=object_type,
                url=jenkins_url,
                job=job,
                version=version,
            )

        super(JenkinsJobNotFoundError, self).__init__(message)


class WrongEnvironmentError(TDSException):
    """Exception for command attempts in incorrect environment"""

    pass


class WrongProjectTypeError(TDSException):
    """Exception for command attempts with incorrect project type"""

    pass
