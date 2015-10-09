"""
REST API view for deployments.
"""

from cornice.resource import resource, view

import tagopsdb.model
import tds.model
from .base import BaseView, init_view

@resource(collection_path="/deployments", path="/deployments/{id}")
@init_view(name="deployment")
class DeploymentView(BaseView):

    param_routes = {}

    defaults = {}

    def _handle_extra_params(self):
        self.valid_attrs.append('force')
        if 'force' in self.request.params:
            if self.request.method != 'PUT':
                self.request.errors.add(
                    'query', 'force',
                    'Force query is only supported for PUT requests.'
                )
                self.request.errors.status = 403
                return
            self.request.validated_params = dict(
                force=self.request.params['force']
            )
            msg = self._validate_boolean('force')
            if msg:
                self.request.errors.add('query', 'force', msg)
                self.request.errors.status = 400
                del self.request.validated_params['force']
                return
            self.forced_queue = self.request.validated_params['force']
            del self.request.validated_params['force']

    def validate_individual_deployment(self, _request):
        self.get_obj_by_name_or_id(param_name='id', can_be_name=False)

    def validate_deployment_delete(self):
        # No deployment validated, can't do any further checks.
        # Should already be a 4xx error response.
        if self.name not in self.request.validated:
            return
        if self.request.validated[self.name].status != 'pending':
            self.request.errors.add(
                'url', 'id',
                "Cannot delete a non-pending deployment. This deployment is "
                "currently in {status} status.".format(
                    status=self.request.validated[self.name].status
                )
            )
            self.request.errors.status = 403
        tier_deps = self.request.validated[self.name].app_deployments
        host_deps = self.request.validated[self.name].host_deployments
        if (tier_deps or host_deps) and not self.request.validated['cascade']:
            self.request.errors.add(
                'url', 'id',
                "Cannot delete deployment with host or tier deployments. "
                "Please use the cascade=true parameter to cascade."
            )
            self.request.errors.add(
                'url', 'to_delete',
                str(dict(
                    host_deployments=[int(x.id) for x in host_deps],
                    tier_deployments=[int(y.id) for y in tier_deps],
                ))
            )
            self.request.errors.status = 403
        self.request.validated['delete_cascade'] = \
            self.request.validated[self.name].host_deployments + \
                self.request.validated[self.name].app_deployments

    def validate_deployment_post(self):
        if 'status' in self.request.validated_params:
            if self.request.validated_params['status'] != 'pending':
                self.request.errors.add(
                    'query', 'status',
                    'Status must be pending for new deployments.'
                )
                self.request.errors.status = 403

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
        if self.name not in self.request.validated:
            return
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
        tier_deployments = self.request.validated[self.name].app_deployments
        host_deployments = self.request.validated[self.name].host_deployments
        if not (tier_deployments or host_deployments):
            self.request.errors.add(
                'query', 'status',
                'Cannot queue deployment with no tier or host deployments.'
            )
            self.request.errors.status = 403
        else:
            for dep in host_deployments:
                conflicting_deps = [host_dep for host_dep in
                    tds.model.HostDeployment.find(
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

        for tier_dep in tier_deployments:
            if tier_dep.package.status != 'completed':
                self.request.errors.add(
                    'query', 'status',
                    'Package with ID {pid} for tier deployment with ID {did} '
                    '(for tier with ID {tid}) is not completed. Please wait '
                    'and verify that the package is completed before '
                    're-attempting.'.format(
                        pid=tier_dep.package_id,
                        did=tier_dep.id,
                        tid=tier_dep.app_id,
                    )
                )
                self.request.errors.status = 403
        for host_dep in host_deployments:
            if host_dep.package.status != 'completed':
                self.request.errors.add(
                    'query', 'status',
                    'Package with ID {pid} for host deployment with ID {did} '
                    '(for host with ID {hid}) is not completed. Please wait '
                    'and verify that the package is completed before '
                    're-attempting.'.format(
                        pid=host_dep.package_id,
                        did=host_dep.id,
                        hid=host_dep.id,
                    )
                )
                self.request.errors.status = 403

        if tier_deployments:
            env_map = {'dev': None, 'staging': 'dev', 'prod': 'staging'}
            for tier_dep in tier_deployments:
                previous_env_short = env_map[tier_dep.environment_obj.env]
                if previous_env_short is None:
                    continue
                previous_env = tagopsdb.Environment.get(env=previous_env_short)
                if previous_env is None:
                    raise tds.exceptions.ProgrammingError(
                        "Could not find environment with short name {env}."
                        .format(env=previous_env_short)
                    )
                previous_tier_dep = tds.model.AppDeployment.find(
                    environment_id=previous_env.id,
                    app_id=tier_dep.app_id,
                    package_id=tier_dep.package_id,
                    status="validated",
                )
                if not previous_tier_dep and not getattr(self, 'forced_queue',
                                                        False):
                    self.request.errors.add(
                        'query', 'status',
                        'Package with ID {id} has not been validated in the '
                        '{env} environment for tier {tier} with ID {tid}. '
                        'Please use force=true to force deployment.'.format(
                            id=tier_dep.package_id,
                            env=previous_env_short,
                            tier=tier_dep.target.name,
                            tid=tier_dep.app_id,
                        )
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
            getattr(self, '_validate_put_status_{status}'.format(
                status=self.request.validated_params['status']
            ), self._validate_put_status_default)()

    @view(validators=('validate_put_post', 'validate_post_required',
                      'validate_obj_post', 'validate_cookie'))
    def collection_post(self):
        self.request.validated_params['user'] = self.request.validated['user']
        return self._handle_collection_post()
