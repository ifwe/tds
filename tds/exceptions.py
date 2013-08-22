#
# Copyright (C) 2012 Tagged, Inc.
#
# All rights reserved

"""Custom exceptions for TagOps deployment program"""


class AccessError(Exception):
    """Exception for access violations (insufficient permissions)"""

    pass


class ConfigurationError(Exception):
    """Exception for invalid or incomplete configuration files"""

    pass


class NoCurrentDeploymentError(Exception):
    """Exception for missing but needed current deployment"""

    pass


class NotImplementedError(Exception):
    """Exception for unimplemented methods"""

    pass


class WrongEnvironmentError(Exception):
    """Exception for command attempts in incorrect environment"""

    pass


class WrongProjectTypeError(Exception):
    """Exception for command attempts with incorrect project type"""

    pass
