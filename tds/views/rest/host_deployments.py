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
        'status': 'choice'
    }

    param_routes = {}

    defaults = {}

    required_post_fields = ('deployment_id', 'host_id',)

    def validate_host_deployment_delete(self):
        if self.validated[self.name].deployment.status != 'pending':
            self.request.errors.add(
                'url', 'id',
                'Cannot delete host deployment whose deployment is no longer '
                'pending.'
            )
            self.request.errors.status = 403

    def validate_individual_host_deployment(self, request):
        self.get_obj_by_name_or_id(obj_type='Host deployment',
                                   model=self.model, param_name='id',
                                   can_be_name=False, dict_name=self.name)

    def validate_host_deployment_put(self):
        self._validate_id("PUT", "host deployment")

    def validate_host_deployment_post(self):
        self._validate_id("POST", "host deployment")

    @view(validators=('validate_put_post', 'validate_post_required',
                      'validate_obj_post', 'validate_cookie'))
    def collection_post(self):
        self.request.validated_params['user'] = self.request.validated['user']
        return self._handle_collection_post()
