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

"""
Abstract base DeployStrategy class.
"""


class DeployStrategy(object):
    """Abstract base DeployStrategy class."""

    def deploy_to_host(self, dep_host, app, version, retry=4):
        """Raise NotImplementedError."""
        raise NotImplementedError

    def restart_host(self, dep_host, app, retry=4):
        """Raise NotImplementedError."""
        raise NotImplementedError
