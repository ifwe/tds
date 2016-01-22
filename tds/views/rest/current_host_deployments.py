"""
REST view for most recent deployment of an application to a host.
"""

from cornice.resource import resource, view

import tds.model
import tagopsdb.model
from .base import BaseView, init_view
from . import types, descriptions
from .urls import ALL_URLS


@resource(path=ALL_URLS['current_host_deployment'])
@init_view(name="current-host-deployment", model=tds.model.HostDeployment,
           set_params=False)
class CurrentHostDeployment(BaseView):
    """
    REST view for most recent deployment of an application to a host.
    """

    param_routes = {}

    individual_allowed_methods = dict(
        GET=dict(description="Get the most recent completed host deployment "
                 "for an application and host."),
    )

    full_types = types.HOST_DEPLOYMENT_TYPES

    full_descriptions = descriptions.HOST_DEPLOYMENT_DESCRIPTIONS

    defaults = {}

    def validate_individual_current_host_deployment(self, request):
        """
        Validate that the application and host being selected exist and that
        there is a deployment of the application on the host.
        If one exists, assign the host deployment to
        request.validated[self.name].
        Add an error otherwise.
        """
        self.get_obj_by_name_or_id('application', tds.model.Application,
                                   'pkg_name')
        self.get_obj_by_name_or_id('host', tds.model.HostTarget,
                                   param_name='host_name_or_id')
        if not all(x in request.validated for x in ('application', 'host')):
            return

        found_assoc = tagopsdb.model.ProjectPackage.find(
            pkg_def_id=request.validated['application'].id,
            app_id=request.validated['host'].app_id,
        )

        if not found_assoc:
            request.errors.add(
                'path', 'host_name_or_id',
                'Association of tier {t_name} of host {h_name} with the '
                'application {a_name} does not exist for any projects.'.format(
                    t_name=request.validated['host'].application.name,
                    h_name=request.validated['host'].name,
                    a_name=request.validated['application'].name,
                )
            )
            request.errors.status = 403
            return

        request.validated[self.name] = request.validated['application'] \
            .get_latest_completed_host_deployment(request.validated['host'].id)
        if not request.validated[self.name]:
            request.errors.add(
                'path', 'host_name_or_id',
                'Completed deployment of application {a_name} on host {h_name} '
                'does not exist.'.format(
                    a_name=request.validated['application'].name,
                    h_name=request.validated['host'].name,
                )
            )
            request.errors.status = 404

    @view(validators=('method_not_allowed',))
    def put(self):
        """
        Method not allowed.
        """
        pass

    @view(validators=('method_not_allowed'))
    def delete(self):
        """
        Method not allowed.
        """
        pass
