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

    def validated_tier_deployment_put(self):
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
        self.validate_id("PUT", "tier deployment")
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
        self._validate_id("POST", "tier deployment")
        self._validate_foreign_key('tier_id', 'tier', tds.model.AppTarget)
        self._validate_foreign_key('environment_id', 'environment',
                                   tagopsdb.model.Environment)
        self._validate_unique_together("POST", "tier deployment")

    @view(validators=('validate_put_post', 'validate_post_required',
                      'validate_obj_post', 'validate_cookie'))
    def collection_post(self):
        self.request.validated_params['user'] = self.request.validated['user']
        return self._handle_collection_post()
