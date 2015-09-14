"""
REST API view for tier deployments.
"""

from cornice.resource import resource, view

import tds.model
import tagopsdb.model
from .base import BaseView, init_view

@resource(collection_path="/tier_deployments", path="/tier_deployments/{id}")
@init_view(name="tier-deployment", model=tds.model.AppDeployment)
class TierDeploymentView(BaseView):

    types = {
        'id': 'integer',
        'deployment_id': 'integer',
        'tier_id': 'integer',
        'status': 'choice',
        'environment_id': 'integer',
    }

    param_routes = {
        'tier_id': 'app_id',
    }

    defaults = {
        'status': 'pending',
    }

    required_post_fields = ('deployment_id', 'tier_id', 'environment_id',)

    unique_together = (
        ('deployment_id', 'tier_id'),
    )

    def validate_tier_deployment_delete(self):
        if self.name not in self.request.validated:
            return
        if self.request.validated[self.name].deployment.status != 'pending':
            self.request.errors.add(
                'path', 'id',
                'Cannot delete tier deployment whose deployment is no longer '
                'pending.'
            )
            self.request.errors.status = 403

    def validate_individual_tier_deployment(self, request):
        self.get_obj_by_name_or_id(obj_type='Tier deployment',
                                   model=self.model, param_name='id',
                                   can_be_name=False, dict_name=self.name)

    def validate_conflicting_env(self, request_type):
        """
        Validate that the user isn't attempting to add or update a tier
        deployment s.t. the associated or attempted to be associated deployment
        has another host or tier deployment in a different environment from
        that of this tier deployment.
        """
        if request_type == 'POST':
            if 'environment_id' not in self.request.validated_params or \
                    'deployment_id' not in self.request.validated_params:
                return
            own_environment = tagopsdb.model.Environment.get(
                id=self.request.validated_params['environment_id']
            )
            deployment = tds.model.Deployment.get(
                id=self.request.validated_params['deployment_id']
            )
            name = 'environment_id'
        elif 'environment_id' not in self.request.validated_params and \
                'deployment_id' not in self.request.validated_params:
            return
        elif self.name not in self.request.validated:
            return
        elif 'environment_id' not in self.request.validated_params:
            own_environment = self.request.validated[self.name].environment_obj
            deployment = tds.model.Deployment.get(
                id=self.request.validated_params['deployment_id']
            )
            name = 'deployment_id'
        elif 'deployment_id' not in self.request.validated_params:
            own_environment = tagopsdb.model.Environment.get(
                id=self.request.validated_params['environment_id']
            )
            deployment = self.request.validated[self.name].deployment
            name = 'environment_id'
        else:
            own_environment = tagopsdb.model.Environment.get(
                id=self.request.validated_params['environment_id']
            )
            deployment = tds.model.Deployment.get(
                id=self.request.validated_params['deployment_id']
            )
            name = 'environment_id'
        if None in (own_environment, deployment):
            return
        for app_dep in deployment.app_deployments:
            if self.name in self.request.validated and app_dep.id == \
                    self.request.validated[self.name].id:
                continue
            if app_dep.environment_id != own_environment.id:
                self.request.errors.add(
                    'query', name,
                    'Cannot deploy to different environments with same '
                    'deployment. There is a tier deployment associated with '
                    'this deployment with ID {app_id} and environment {env}.'
                    .format(app_id=app_dep.id, env=app_dep.environment)
                )
                self.request.errors.status = 409
        for host_dep in deployment.host_deployments:
            if host_dep.host.environment_id != own_environment.id:
                self.request.errors.add(
                    'query', name,
                    'Cannot deploy to different environments with same '
                    'deployment. There is a host deployment associated with '
                    'this deployment with ID {tier_id} and environment {env}.'
                    .format(tier_id=host_dep.id, env=host_dep.host.environment)
                )
                self.request.errors.status = 409

    def validate_tier_deployment_put(self):
        if self.name not in self.request.validated:
            return
        if self.request.validated[self.name].deployment.status != 'pending':
            self.request.errors.add(
                'path', 'id',
                'Users cannot modify tier deployments whose deployments are no'
                ' longer pending.'
            )
            self.request.errors.status = 403
            return
        if 'status' in self.request.validated_params:
            self.request.errors.add(
                'query', 'status',
                "Users cannot change the status of tier deployments."
            )
            self.request.errors.status = 403
        self.validate_conflicting_env('PUT')
        self._validate_id("PUT", "tier deployment")
        self._validate_foreign_key('tier_id', 'tier', tds.model.AppTarget)
        self._validate_foreign_key('environment_id', 'environment',
                                   tagopsdb.model.Environment)
        self._validate_unique_together("PUT", "tier deployment")

    def validate_tier_deployment_post(self):
        if 'status' in self.request.validated_params:
            if self.request.validated_params['status'] != 'pending':
                self.request.errors.add(
                    'query', 'status',
                    'Status must be pending for new tier deployments.'
                )
                self.request.errors.status = 403
        self.validate_conflicting_env('POST')
        self._validate_id("POST", "tier deployment")
        self._validate_foreign_key('tier_id', 'tier', tds.model.AppTarget)
        self._validate_foreign_key('environment_id', 'environment',
                                   tagopsdb.model.Environment)
        self._validate_unique_together("POST", "tier deployment")

    @view(validators=('validate_put_post', 'validate_post_required',
                      'validate_obj_post', 'validate_cookie'))
    def collection_post(self):
        for host in tds.model.HostTarget.find(
            app_id=self.request.validated_params['tier_id'],
            environment_id=self.request.validated_params['environment_id']
        ):
            host_dep = tds.model.HostDeployment.create(
                host_id=host.id,
                deployment_id=self.request.validated_params['deployment_id'],
                user=self.request.validated['user'],
                status='pending',
            )
        self.request.validated_params['user'] = self.request.validated['user']
        return self._handle_collection_post()
