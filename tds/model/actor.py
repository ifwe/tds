"""Model module for actor object."""

import grp
import os
import pwd

from .base import Base


class Actor(Base):
    """Model base class for actor object."""

    def __init__(self, name, groups):
        """Initialize object."""
        super(Actor, self).__init__()
        self.name = name
        self.groups = groups


class LocalActor(Actor):
    """Model class for actor object populated with values from the local OS."""

    def __init__(self):
        """Initialize object."""
        super(LocalActor, self).__init__(
            pwd.getpwuid(os.getuid()).pw_name,
            [grp.getgrgid(group).gr_name for group in os.getgroups()]
        )
