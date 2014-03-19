'''Model module for actor object'''

import grp
import os
import pwd

from .base import Base


class Actor(Base):
    'Model class for actor object'

    @property
    def name(self):
        'Return name of user'
        return pwd.getpwuid(os.getuid())[0]

    @property
    def groups(self):
        'Return groups for user'
        return [grp.getgrgid(group).gr_name for group in os.getgroups()]
