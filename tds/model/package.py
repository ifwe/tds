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

"""Model module for package object."""

from .base import Base
import tagopsdb


class Package(Base):
    """Represents a deployable package for a version of an application."""
    # name
    # version
    # application

    delegate = tagopsdb.Package

    def check_app_deployments(self, tier, environment):
        """
        Check for an existing validated deployment for a given tier
        and environment; this is just a boolean check
        """

        for app_dep in self.delegate.app_deployments:
            if (app_dep.target == tier.delegate and
                app_dep.environment_obj.env == environment and
                app_dep.status == 'validated'):
                return True

        return False

    def get_current_app_deployment(self, tier_id, environment_id, query=None):
        if query is None:
            query = tagopsdb.Session.query(tagopsdb.model.AppDeployment)
        return query.filter(
            tagopsdb.model.AppDeployment.package_id == self.id,
            tagopsdb.model.AppDeployment.app_id == tier_id,
            tagopsdb.model.AppDeployment.environment_id == environment_id,
        ).order_by(desc(tagopsdb.model.AppDeployment.realized)).first()
