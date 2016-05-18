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

"""Model module for project object."""

from .base import Base
import tagopsdb


class Project(Base):
    """A project links applications together in a deployable group."""
    # name
    # applications (aka package_definitions)

    delegate = tagopsdb.Project

    @property
    def applications(self):
        """Alias for package_definitions."""
        return self.package_definitions

    @property
    def targets(self):
        """Return deploy targets, but ignore the "dummy" target."""
        from .deploy_target import AppTarget
        return [
            AppTarget(delegate=x)
            for x in self.delegate.targets
            if x.name != x.dummy
        ]
