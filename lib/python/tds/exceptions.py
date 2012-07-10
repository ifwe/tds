#
# Copyright (C) 2012 Tagged, Inc.
#
# All rights reserved

"""Custom exceptions for TagOps deployment program"""


class AccessError(Exception):
    """Exception for access violations (insufficient permissions)"""

    pass


class NotImplementedError(Exception):
    """Exception for unimplemented methods"""

    pass


class WrongEnvironmentError(Exception):
    """Exception for command attempts in incorrect environment"""

    pass
