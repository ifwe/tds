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
REST API view for host deployments.
"""

from cornice.resource import resource, view

import tds.model
import tagopsdb.model
from .base import BaseView, init_view
from .urls import ALL_URLS
from .permissions import HOST_DEPLOYMENT_PERMISSIONS


@resource(collection_path=ALL_URLS['host_deployment_collection'],
          path=ALL_URLS['host_deployment'])
@init_view(name="host-deployment", model=tds.model.HostDeployment)
class HostDeploymentView(BaseView):
    """
    View for host deployments.
    """

    param_routes = {}

    defaults = {
        'status': 'pending',
    }

    required_post_fields = ('deployment_id', 'host_id', 'package_id')

    unique_together = (
        ('deployment_id', 'host_id', 'package_id'),
    )

    permissions = HOST_DEPLOYMENT_PERMISSIONS

    individual_allowed_methods = dict(
        GET=dict(description="Get host deployment matching ID."),
        HEAD=dict(description="Do a GET query without a body returned."),
        PUT=dict(description="Update host deployment matching ID."),
        DELETE=dict(description="Delete host deployment matching ID."),
    )

    collection_allowed_methods = dict(
        GET=dict(description="Get a list of host deployments, optionally by "
                 "limit and/or start."),
        HEAD=dict(description="Do a GET query without a body returned."),
        POST=dict(description="Add a new host deployment."),
    )

    def validate_host_deployment_delete(self):
        """
        Validate that it's okay to delete the host deployment at
        self.request.validated[self.name].
        """
        if self.name not in self.request.validated:
            return
        if self.request.validated[self.name].deployment.status != 'pending':
            self.request.errors.add(
                'path', 'id',
                'Cannot delete host deployment whose deployment is no longer '
                'pending.'
            )
            self.request.errors.status = 403
            return
        found_app_dep = self.query(tds.model.AppDeployment).get(
            deployment_id=self.request.validated[self.name].deployment_id,
            app_id=self.request.validated[self.name].host.app_id,
        )
        if found_app_dep is not None and not self.request.validated['cascade']:
            self.request.errors.add(
                'query', '',
                'Cannot delete a host deployment that is part of a tier '
                'deployment. Please use cascade=true to delete this host '
                'deployment and its associated tier deployment.'
            )
            self.request.errors.add(
                'url', 'to_delete',
                str(dict(tier_deployment=int(found_app_dep.id)))
            )
            self.request.errors.status = 403
        elif found_app_dep is not None:
            self.request.validated['delete_cascade'] = [found_app_dep]

    def validate_individual_host_deployment(self, _request):
        """
        Validate that the host deployment being retrieved exists.
        """
        self.get_obj_by_name_or_id(obj_type='Host deployment',
                                   model=self.model, param_name='id',
                                   can_be_name=False, dict_name=self.name)

    def validate_conflicting_env(self, request_type):
        """
        Validate that the user isn't attempting to add or update a host
        deployment s.t. the associated or attempted to be associated deployment
        has another tier or host deployment in a different environment from
        that of this host deployment.
        """
        if request_type == 'POST':
            if 'host_id' not in self.request.validated_params or \
                    'deployment_id' not in self.request.validated_params:
                return
            own_host = self.query(tds.model.HostTarget).get(
                id=self.request.validated_params['host_id']
            )
            deployment = self.query(tds.model.Deployment).get(
                id=self.request.validated_params['deployment_id']
            )
            name = 'host_id'
        elif 'host_id' not in self.request.validated_params and \
                'deployment_id' not in self.request.validated_params:
            return
        elif self.name not in self.request.validated:
            return
        elif 'host_id' not in self.request.validated_params:
            own_host = self.request.validated[self.name].host
            deployment = self.query(tds.model.Deployment).get(
                id=self.request.validated_params['deployment_id']
            )
            name = 'deployment_id'
        elif 'deployment_id' not in self.request.validated_params:
            own_host = self.query(tds.model.HostTarget).get(
                id=self.request.validated_params['host_id']
            )
            deployment = self.request.validated[self.name].deployment
            name = 'host_id'
        else:
            own_host = self.query(tds.model.HostTarget).get(
                id=self.request.validated_params['host_id']
            )
            deployment = self.query(tds.model.Deployment).get(
                id=self.request.validated_params['deployment_id']
            )
            name = 'host_id'
        if None in (own_host, deployment):
            return
        for app_dep in deployment.app_deployments:
            if app_dep.environment_id != own_host.environment_id:
                self.request.errors.add(
                    'query', name,
                    'Cannot deploy to different environments with same '
                    'deployment. There is a tier deployment associated with '
                    'this deployment with ID {app_id} and environment {env}.'
                    .format(app_id=app_dep.id, env=app_dep.environment)
                )
                self.request.errors.status = 409
        for host_dep in deployment.host_deployments:
            if self.name in self.request.validated and host_dep.id == \
                    self.request.validated[self.name].id:
                continue
            if host_dep.host.environment_id != own_host.environment_id:
                self.request.errors.add(
                    'query', name,
                    'Cannot deploy to different environments with same '
                    'deployment. There is a host deployment associated with '
                    'this deployment with ID {host_id} and environment {env}.'
                    .format(host_id=host_dep.id, env=host_dep.host.environment)
                )
                self.request.errors.status = 409

    def validate_host_deployment_put(self):
        """
        Validate a PUT request for a host deployment.
        """
        if self.name not in self.request.validated:
            return
        if self.request.validated[self.name].deployment.status != 'pending':
            self.request.errors.add(
                'path', 'id',
                'Users cannot modify host deployments whose deployments are no'
                ' longer pending.'
            )
            self.request.errors.status = 403
            return
        if 'status' in self.request.validated_params:
            self.request.errors.add(
                'query', 'status',
                "Users cannot change the status of host deployments."
            )
            self.request.errors.status = 403
        self.validate_conflicting_env('PUT')
        self._validate_foreign_key('host_id', 'host', tds.model.HostTarget)
        self._validate_foreign_key('package_id', 'package', tds.model.Package)
        self._validate_unique_together("PUT", "host deployment")
        # If the package_id is being changed and the deployment isn't pending:
        if 'package_id' in self.request.validated_params and \
                self.request.validated_params['package_id'] != \
                self.request.validated[self.name].package_id and \
                self.request.validated[self.name].deployment.status != \
                'pending':
            self.request.errors.add(
                'query', 'package_id',
                'Cannot change package_id for a host deployment with a '
                'non-pending deployment.'
            )
            self.request.errors.status = 403
        if not any(
            x in self.request.validated_params for x in ('host_id',
                                                         'package_id')
        ):
            return
        pkg_id = self.request.validated_params['package_id'] if 'package_id' \
            in self.request.validated_params else \
            self.request.validated[self.name].package_id
        host_id = self.request.validated_params['host_id'] if 'host_id' in \
            self.request.validated_params else \
            self.request.validated[self.name].host_id
        self._validate_project_package(pkg_id, host_id)

    def _validate_project_package(self, pkg_id, host_id):
        """
        Validate that the tier for the host with ID host_id is associated with
        the application for the package with ID pkg_id for some project.
        If it isn't, add an error.
        """
        found_pkg = self.query(tds.model.Package).get(id=pkg_id)
        found_host = self.query(tds.model.HostTarget).get(id=host_id)
        if not (found_pkg and found_host):
            return
        found_project_pkg = self.query(
            tagopsdb.model.ProjectPackage
        ).find(
            pkg_def_id=found_pkg.pkg_def_id,
            app_id=found_host.app_id,
        )
        if not found_project_pkg:
            self.request.errors.add(
                'query', 'host_id' if 'host_id' in self.request.validated_params
                else 'package_id',
                'Tier {t_name} of host {h_name} is not associated with the '
                'application {a_name} for any projects.'.format(
                    t_name=found_host.application.name,
                    h_name=found_host.name,
                    a_name=found_pkg.application.name,
                )
            )
            self.request.errors.status = 403

    def validate_host_deployment_post(self):
        """
        Validate a POST of a new host deployment.
        """
        if 'status' in self.request.validated_params:
            if self.request.validated_params['status'] != 'pending':
                self.request.errors.add(
                    'query', 'status',
                    'Status must be pending for new host deployments.'
                )
                self.request.errors.status = 403
        self.validate_conflicting_env('POST')
        self._validate_foreign_key('host_id', 'host', tds.model.HostTarget)
        self._validate_foreign_key('package_id', 'package', tds.model.Package)
        self._validate_unique_together("POST", "host deployment")
        if not all(
            x in self.request.validated_params for x in ('package_id',
                                                         'host_id')
        ):
            return
        self._validate_project_package(
            self.request.validated_params['package_id'],
            self.request.validated_params['host_id'],
        )

    def validate_env_restrictions(self, request):
        """
        Validate that the cookie is authorized to deploy to environment of this
        host dep.
        """
        if 'environments' in request.restrictions:
            if 'host_id' in request.validated_params:
                host = self.query(tds.model.HostTarget).get(
                    id=request.validated_params['host_id'],
                )
            elif self.name in request.validated:
                host = request.validated[self.name]
            else:
                return

            if host is not None and str(host.environment_id) not in \
                    request.restrictions['environments']:
                request.errors.add(
                    'header', 'cookie',
                    "Insufficient authorization. This cookie only has "
                    "permissions for the following environment IDs: "
                    "{environments}.".format(
                        environments=sorted(
                            int(env_id) for env_id in request.restrictions[
                                'environments'
                            ]
                        ),
                    )
                )
                request.errors.status = 403

    @view(validators=('validate_put_post', 'validate_post_required',
                      'validate_obj_post', 'validate_cookie',
                      'validate_env_restrictions'))
    def collection_post(self):
        """
        Perform a collection POST after all validation has passed.
        """
        self.request.validated_params['user'] = self.request.validated['user']
        return self._handle_collection_post()

    @view(validators=('validate_individual', 'validate_put_post',
                      'validate_obj_put', 'validate_cookie',
                      'validate_env_restrictions'))
    def put(self):
        """
        Handle a PUT request after the parameters are marked valid JSON.
        """
        for attr in self.request.validated_params:
            setattr(
                self.request.validated[self.name],
                self.param_routes.get(attr, attr),
                self.request.validated_params[attr],
            )
        self.session.commit()
        return self.make_response(
            self.to_json_obj(self.request.validated[self.name])
        )
