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


class ConfigurationError(TDSException):
    """Exception for invalid or incomplete configuration files"""

    pass


class FailedConnectionError(TDSException):
    """Exception for when connections with Jenkins, etc. fail."""

    pass


class InvalidInputError(TDSException):
    """Exception for invalid input from user."""

    pass


class NotFoundError(TDSException):
    """Exception for when an item is not found or does not exist."""

    pass


class WrongEnvironmentError(TDSException):
    """Exception for command attempts in incorrect environment"""

    pass


class WrongProjectTypeError(TDSException):
    """Exception for command attempts with incorrect project type"""

    pass
