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

"""Model module for deploy_info object."""

from .base import Base


class DeployInfo(Base):
    """Model base class for actor object."""

    def __init__(self, actor, action, project, package, target):
        """Initialize object."""
        super(DeployInfo, self).__init__()
        self.actor = actor
        self.action = action
        self.project = project
        self.package = package
        self.target = target
