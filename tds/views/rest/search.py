"""
REST API object search view.
"""

from cornice.resource import resource, view

import tagopsdb.model
import tds.model
from . import obj_types, descriptions, base
from .urls import ALL_URLS
from .permissions import SEARCH_PERMISSIONS


@resource(path=ALL_URLS['search'])
class SearchView(base.BaseView):
    """
    Search view. Only supported method is GET.
    obj_type should be one of the keys of SearchView.TYPES below.
    """

    name = 'search'

    permissions = SEARCH_PERMISSIONS

    APPLICATION_DICT = {
        'model': tds.model.Application,
        'params': obj_types.APPLICATION_TYPES,
        'param_routes': {
            'name': 'pkg_name',
            'job': 'path',
        },
        'descriptions': descriptions.APPLICATION_DESCRIPTIONS,
    }

    APPLICATION_TIER_DICT = {
        'model': tagopsdb.model.ProjectPackage,
        'params': obj_types.APPLICATION_TIER_TYPES,
        'param_routes': {
            'application_id': 'pkg_def_id',
            'tier_id': 'app_id',
        },
        'descriptions': descriptions.APPLICATION_TIER_DESCRIPTIONS,
    }

    DEPLOYMENT_DICT = {
        'model': tds.model.Deployment,
        'params': obj_types.DEPLOYMENT_TYPES,
        'param_routes': {},
        'descriptions': descriptions.DEPLOYMENT_DESCRIPTIONS,
    }

    ENVIRONMENT_DICT = {
        'model': tagopsdb.model.Environment,
        'params': obj_types.ENVIRONMENT_TYPES,
        'param_routes': {
            'name': 'environment',
            'short_name': 'env',
        },
        'descriptions': descriptions.ENVIRONMENT_DESCRIPTIONS,
    }

    GANGLIA_DICT = {
        'model': tagopsdb.model.Ganglia,
        'params': obj_types.GANGLIA_TYPES,
        'param_routes': {
            'name': 'cluster_name',
        },
        'descriptions': descriptions.GANGLIA_DESCRIPTIONS,
    }

    HIPCHAT_DICT = {
        'model': tagopsdb.model.Hipchat,
        'params': obj_types.HIPCHAT_TYPES,
        'param_routes': {
            'name': 'room_name',
        },
        'descriptions': descriptions.HIPCHAT_DESCRIPTIONS,
    }

    HOST_DICT = {
        'model': tds.model.HostTarget,
        'params': obj_types.HOST_TYPES,
        'param_routes': {
            'name': 'hostname',
            'cage': 'cage_location',
            'cab': 'cab_location',
            'rack': 'rack_location',
            'tier_id': 'app_id',
        },
        'descriptions': descriptions.HOST_DESCRIPTIONS,
    }

    HOST_DEPLOYMENT_DICT = {
        'model': tds.model.HostDeployment,
        'params': obj_types.HOST_DEPLOYMENT_TYPES,
        'param_routes': {},
        'descriptions': descriptions.HOST_DEPLOYMENT_DESCRIPTIONS,
    }

    PACKAGE_DICT = {
        'model': tds.model.Package,
        'params': obj_types.PACKAGE_TYPES,
        'param_routes': {
            'application_id': 'pkg_def_id',
        },
        'descriptions': descriptions.PACKAGE_DESCRIPTIONS,
    }

    PROJECT_DICT = {
        'model': tds.model.Project,
        'params': obj_types.PROJECT_TYPES,
        'param_routes': {},
        'descriptions': descriptions.PROJECT_DESCRIPTIONS,
    }

    TIER_DICT = {
        'model': tds.model.AppTarget,
        'params': obj_types.TIER_TYPES,
        'param_routes': {
            'name': 'app_type',
            'ganglia_name': 'ganglia_group_name',
        },
        'descriptions': descriptions.TIER_DESCRIPTIONS,
    }

    TIER_DEPLOYMENT_DICT = {
        'model': tds.model.AppDeployment,
        'params': obj_types.TIER_DEPLOYMENT_TYPES,
        'param_routes': {
            'tier_id': 'app_id',
        },
        'descriptions': descriptions.TIER_DEPLOYMENT_DESCRIPTIONS,
    }

    TYPES = {
        'applications': APPLICATION_DICT,
        'application_tiers': APPLICATION_TIER_DICT,
        'deployments': DEPLOYMENT_DICT,
        'environments': ENVIRONMENT_DICT,
        'ganglias': GANGLIA_DICT,
        'hipchats': HIPCHAT_DICT,
        'hosts': HOST_DICT,
        'host_deployments': HOST_DEPLOYMENT_DICT,
        'packages': PACKAGE_DICT,
        'projects': PROJECT_DICT,
        'tiers': TIER_DICT,
        'tier_deployments': TIER_DEPLOYMENT_DICT,
    }

    def _get_results(self):
        """
        Set self.results to the results of the query in
        self.request.validated_params.
        """
        if self.request.errors:
            return
        self.results = self.query(self.model)
        if self.request.validated_params:
            self.results = self.results.filter_by(
                **self.request.validated_params
            )

        if self.start is not None:
            self.results = self.results.filter(
                self.model.id >= self.start
            )

        if self.limit is not None:
            self.results = self.results.limit(self.limit)

    def _validate_obj_type_exists(self):
        """
        If the obj_type is in the self.types, return True.
        Otherwise, add an error and return False.
        """
        if self.request.matchdict['obj_type'] not in self.TYPES:
            self.request.errors.add(
                'path', 'obj_type',
                "Unknown object type {obj_type}. Supported object types are: "
                "{types}.".format(
                    obj_type=self.request.matchdict['obj_type'],
                    types=sorted(self.TYPES.keys()),
                )
            )
            self.request.errors.status = 404
            return False
        return True

    def _get_param_choices(self, param):
        """
        Return all param choices for a param with type 'choice'.
        Get them from self.obj_dict if possible.
        Otherwise, get them from the column's enums in the database table.
        """
        choice_param = '{param}_choices'.format(param=param)
        if choice_param in self.obj_dict:
            return self.obj_dict[choice_param]
        else:
            try:
                if getattr(self.model, 'delegate', None):
                    table = self.model.delegate.__table__
                else:
                    table = self.model.__table__
                col_name = param
                if param in self.obj_dict['param_routes']:
                    col_name = self.obj_dict['param_routes'][param]
                return table.columns[col_name].type.enums
            except Exception as exc:
                raise tds.exceptions.ProgrammingError(
                    "No choices set for param {param}. "
                    "Got exception {e}.".format(param=param, e=exc)
                )

    def validate_search_get(self, request):
        """
        Validate a search GET request.
        """
        self.name = 'search'
        if not self._validate_obj_type_exists():
            return

        self.obj_dict = self.TYPES[request.matchdict['obj_type']]
        self.model = self.obj_dict['model']
        self._validate_params(
            self.obj_dict['params'].keys() + ['limit', 'start', 'select']
        )

        for param in request.validated_params:
            if param not in self.obj_dict['params']:
                continue
            if self.obj_dict['params'][param] == 'choice':
                choice_param = '{param}_choices'.format(param=param)
                setattr(self, choice_param, self._get_param_choices(param))

        self._validate_json_params(self.obj_dict['params'])
        self._validate_json_params(
            {'limit': 'integer', 'start': 'integer', 'select': 'string'}
        )
        self.limit = self.start = None
        if 'limit' in request.validated_params:
            self.limit = request.validated_params.pop('limit')
        if 'start' in request.validated_params:
            self.start = request.validated_params.pop('start')
        self._validate_select_attributes(
            request, self.obj_dict['params'].keys()
        )
        self._route_params(self.obj_dict['param_routes'])
        self._get_results()

    def validate_search_options(self, request):
        """
        Validate search OPTIONS request.
        """
        if not self._validate_obj_type_exists():
            return
        self.obj_dict = self.TYPES[request.matchdict['obj_type']]
        self.model = self.obj_dict['model']
        self.result = dict(
            GET=dict(
                description="Search for {obj_type} by specifying restrictions "
                    "on parameters.".format(
                        obj_type=request.matchdict['obj_type'].replace('_',
                                                                       ' ')
                    ),
                parameters=dict(),
            ),
            HEAD=dict(description="Do a GET query without a body returned."),
            OPTIONS=dict(
                description="Get HTTP method options and parameters for this "
                    "URL endpoint.",
            ),
        )
        for key in self.obj_dict['params']:
            self.result['GET']['parameters'][key] = dict(
                type=self.obj_dict['params'][key],
                description=self.obj_dict['descriptions'][key]
            )
            if self.obj_dict['params'][key] == 'choice':
                self.result['GET']['parameters'][key]['choices'] = \
                    self._get_param_choices(key)

    @view(validators=('validate_search_get', 'validate_cookie'))
    def get(self):
        """
        Perform a GET request after all validation has passed.
        """
        if 'Expect' in self.request.headers:
            if self.request.headers['Expect'] in ("302 Found",
                                                  "303 See Other"):
                if len(self.results.all()) == 1:
                    return self.make_response(
                        body='',
                        status=self.request.headers['Expect'],
                        headers=dict(
                            Location="{app_path}/{obj_type}/{obj_id}".format(
                                app_path=self.request.application_url,
                                obj_type=self.request.matchdict['obj_type'],
                                obj_id=self.results[0].id,
                            )
                        )
                    )
                else:
                    return self.make_response(
                        body='',
                        status="417 Expectation Failed",
                    )
            elif self.request.headers['Expect'] != "200 OK":
                return self.make_response(
                    body='',
                    status="417 Expectation Failed",
                )
        return self.make_response([
            self.to_json_obj(x, self.obj_dict['param_routes']) for x in
            self.results
        ])

    @view(validators=('validate_search_options',))
    def options(self):
        """
        Perform an OPTIONS request after all validation has passed.
        """
        return self.make_response(
            body=self.to_json_obj(self.result),
            headers=dict(Allows="GET, HEAD, OPTIONS"),
        )

    @view(validators=('method_not_allowed'))
    def delete(self):
        """
        Perform a DELETE request after all validation has passed.
        """
        return self.make_response({})

    @view(validators=('method_not_allowed'))
    def put(self):
        """
        Perform a PUT after all validation has passed.
        """
        return self.make_response({})
