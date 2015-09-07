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

    def _validate_put_status_canceled(self):
        """
        Case status is being updated to canceled.
        """
        if self.request.validated[self.name].status not in (
            'queued', 'inprogress', 'canceled'
        ):
            self.request.errors.add(
                'query', 'status',
                'Cannot change status to canceled from {status}.'.format(
                    status=self.request.validated[self.name].status
                )
            )
            self.request.errors.status = 403

    def _validate_put_status_queued(self):
        """
        Case status is being updated to queued.
        """
        if self.request.validated[self.name].status in (
            'canceled', 'inprogress', 'complete'
        ):
            self.request.errors.add(
                'query', 'status',
                'Cannot change status to queued from {status}.'.format(
                    status=self.request.validated[self.name].status
                )
            )
            self.request.errors.status = 403
        app_deployments = self.request.validated[self.name].app_deployments
        host_deployments = self.request.validated[self.name].host_deployments
        if not (app_deployments or host_deployments):
            self.request.errors.add(
                'query', 'status',
                'Cannot queue deployment with no tier or host deployments.'
            )
            self.request.errors.status = 403
        else:
            for dep in host_deployments:
                conflicting_deps = [host_dep for host_dep in
                    tds.model.HostDeployment.get(
                        host_id=dep.host_id,
                    ) if host_dep.id != dep.id and host_dep.deployment.status
                    in ('queued', 'inprogress')
                ]
                if conflicting_deps:
                    self.request.errors.add(
                        'query', 'status',
                        'Cannot queue deployment. There are currently other '
                        'queued or in progress deployments for host '
                        '{host_name}.'.format(host_name=dep.host.name)
                    )
                    self.request.errors.status = 403

    def _validate_put_status_pending(self):
        """
        Case status is being updated to pending.
        """
        if self.request.validated[self.name].status != 'pending':
            self.request.errors.add(
                'query', 'status',
                'Cannot change status to pending from {status}.'.format(
                    status=self.request.validated[self.name].status
                )
            )
            self.request.errors.status = 403

    def _validate_put_status_default(self):
        """
        Case status is being updated to something other than canceled, pending,
        or queued.
        """
        self.request.errors.add(
            'query', 'status',
            'Users cannot change status to {status}.'.format(
                status=self.request.validated_params['status']
            )
        )
        self.request.errors.status = 403

    def validate_deployment_put(self):
        if 'status' in self.request.validated_params:
            validator = getattr(self, '_validate_put_status_{status}'.format(
                status=self.request.validated_params['status']
            ), self._validate_put_status_default)
            validator()
        if 'package_id' in self.request.validated_params and \
                self.request.validated_params['package_id'] != \
                self.request.validated[self.name].package_id and \
                self.request.validated[self.name].status != 'pending':
            self.request.errors.add(
                'query', 'package_id',
                'Cannot change package_id for a non-pending deployment.'
            )
        self._validate_id("PUT")

    @view(validators=('validate_put_post', 'validate_post_required',
                      'validate_cookie'))
    def collection_post(self):
        self.request.validated_params['user'] = self.request.validated['user']
        return self._handle_collection_post()
