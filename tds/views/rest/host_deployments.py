"""
REST API view for host deployments.
"""

from cornice.resource import resource, view

import tds.model
from .base import BaseView, init_view

@resource(collection_path="/host_deployments", path="/host_deployments/{id}")
@init_view(name="host-deployment", model=tds.model.HostDeployment)
class HostDeploymentView(BaseView):

    types = {
        'id': 'integer',
        'deployment_id': 'integer',
        'host_id': 'integer',
        'status': 'choice',
    }

    param_routes = {}

    defaults = {
        'status': 'pending',
    }

    required_post_fields = ('deployment_id', 'host_id',)

    unique_together = (
        ('deployment_id', 'host_id'),
    )

    def validate_host_deployment_delete(self):
        if self.name not in self.request.validated:
            return
        if self.request.validated[self.name].deployment.status != 'pending':
            self.request.errors.add(
                'path', 'id',
                'Cannot delete host deployment whose deployment is no longer '
                'pending.'
            )
            self.request.errors.status = 403

    def validate_individual_host_deployment(self, request):
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
            own_host = tds.model.HostTarget.get(
                id=self.request.validated_params['host_id']
            )
            deployment = tds.model.Deployment.get(
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
            deployment = tds.model.Deployment.get(
                id=self.request.validated_params['deployment_id']
            )
            name = 'deployment_id'
        elif 'deployment_id' not in self.request.validated_params:
            own_host = tds.model.HostTarget.get(
                id=self.request.validated_params['host_id']
            )
            deployment = self.request.validated[self.name].deployment
            name = 'host_id'
        else:
            own_host = tds.model.HostTarget.get(
                id=self.request.validated_params['host_id']
            )
            deployment = tds.model.Deployment.get(
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
        self._validate_id("PUT", "host deployment")
        self._validate_foreign_key('host_id', 'host', tds.model.HostTarget)
        self._validate_unique_together("PUT", "host deployment")

    def validate_host_deployment_post(self):
        if 'status' in self.request.validated_params:
            if self.request.validated_params['status'] != 'pending':
                self.request.errors.add(
                    'query', 'status',
                    'Status must be pending for new host deployments.'
                )
                self.request.errors.status = 403
        self.validate_conflicting_env('POST')
        self._validate_id("POST", "host deployment")
        self._validate_foreign_key('host_id', 'host', tds.model.HostTarget)
        self._validate_unique_together("POST", "host deployment")

    @view(validators=('validate_put_post', 'validate_post_required',
                      'validate_obj_post', 'validate_cookie'))
    def collection_post(self):
        self.request.validated_params['user'] = self.request.validated['user']
        return self._handle_collection_post()
