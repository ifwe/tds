"""
REST API view for deployments.
"""

from cornice.resource import resource, view

import tds.model
from .base import BaseView, init_view

@resource(collection_path="/deployments", path="/deployments/{id}")
@init_view(name="deployment")
class DeploymentView(BaseView):

    types = {
        'id': 'integer',
        'package_id': 'integer',
        'status': 'choice',
    }

    param_routes = {}

    defaults = {}

    required_post_fields = ('package_id',)

    def validate_individual_deployment(self, request):
        self.get_obj_by_name_or_id(param_name='id', can_be_name=False)

    def validate_deployment_post(self):
        if 'status' in self.request.validated_params:
            if self.request.validated_params['status'] != 'pending':
                self.request.errors.add(
                    'query', 'status',
                    'Status must be "pending" for new deployments.'
                )
                self.request.errors.status = 403
        self._validate_id("POST")

    def validate_deployment_put(self):
        self._validate_id("PUT")

    @view(validators=('validate_put_post', 'validate_post_required',
                      'validate_cookie'))
    def collection_post(self):
        self.request.validated_params['user'] = self.request.validated['user']
        return self._handle_collection_post()
