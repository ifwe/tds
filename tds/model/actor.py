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
