"""
REST API object search view.
"""

from cornice.resource import resource, view

import tagopsdb.model
import tds.model
from . import base

@resource(path="/search/{obj_type}")
class SearchView(base.BaseView):
    """
    Search view. Only supported method is GET.
    obj_type should be one of the keys of SearchView.TYPES below.
    """

    APPLICATION_DICT = {
        'model': tds.model.Application,
        'params': {
            'id': 'integer',
            'name': 'string',
            'job': 'string',
            'build_host': 'string',
            'build_type': 'choice',
            'deploy_type': 'string',
            'arch': 'choice',
            'validation_type': 'string',
            'env_specific': 'boolean',
        },
        'param_routes': {
            'name': 'pkg_name',
            'job': 'path',
        },
    }

    DEPLOYMENT_DICT = {
        'model': tds.model.Deployment,
        'params': {
            'id': 'integer',
            'package_id': 'integer',
            'user': 'string',
            'status': 'choice',
        },
        'param_routes': {},
    }

    GANGLIA_DICT = {
        'model': tagopsdb.model.Ganglia,
        'params': {
            'id': 'integer',
            'name': 'string',
            'port': 'integer',
        },
        'param_routes': {
            'name': 'cluster_name',
        },
    }

    HIPCHAT_DICT = {
        'model': tagopsdb.model.Hipchat,
        'params': {
            'id': 'integer',
            'name': 'string',
        },
        'param_routes': {
            'name': 'room_name',
        },
    }

    HOST_DICT = {
        'model': tds.model.HostTarget,
        'params': {
            'id': 'integer',
            'name': 'string',
            'tier_id': 'integer',
            'cage': 'integer',
            'cab': 'string',
            'rack': 'integer',
            'kernel_version': 'string',
            'console_port': 'string',
            'power_port': 'string',
            'power_circuit': 'string',
            'state': 'choice',
            'arch': 'choice',
            'distribution': 'choice',
            'timezone': 'string',
            'environment_id': 'integer',
        },
        'param_routes': {
            'name': 'hostname',
            'cage': 'cage_location',
            'cab': 'cab_location',
            'rack': 'rack_location',
            'tier_id': 'app_id',
        },
        'arch_choices': ('i386', 'noarch', 'x86_64',),
        'distribution_choices': (
            'centos5.4', 'centos6.2', 'centos6.4', 'centos6.5',
            'centos7.0', 'centos7.1', 'fedora18', 'rhel5.3', 'rhel6.2',
            'rhel6.3', 'rhel6.4', 'rhel6.5', 'ontap',
        ),
    }

    HOST_DEPLOYMENT_DICT = {
        'model': tds.model.HostDeployment,
        'params': {
            'id': 'integer',
            'deployment_id': 'integer',
            'host_id': 'integer',
            'status': 'choice',
            'user': 'string',
        },
        'param_routes': {},
    }

    PACKAGE_DICT = {
        'model': tds.model.Package,
        'params': {
            'id': 'integer',
            'version': 'integer',
            'revision': 'integer',
            'status': 'choice',
            'builder': 'choice',
            'job': 'string',
        },
        'param_routes': {},
    }

    PROJECT_DICT = {
        'model': tds.model.Project,
        'params': {
            'id': 'number',
            'name': 'string',
        },
        'param_routes': {},
    }

    TIER_DICT = {
        'model': tds.model.AppTarget,
        'params': {
            'id': 'integer',
            'name': 'string',
            'distribution': 'choice',
            'puppet_class': 'string',
            'ganglia_id': 'integer',
            'ganglia_name': 'string',
            'status': 'choice',
        },
        'param_routes': {
            'name': 'app_type',
            'ganglia_name': 'ganglia_group_name',
        },
    }

    TIER_DEPLOYMENT_DICT = {
        'model': tds.model.AppDeployment,
        'params': {
            'id': 'integer',
            'deployment_id': 'integer',
            'tier_id': 'integer',
            'status': 'choice',
            'environment_id': 'integer',
            'user': 'string',
        },
        'param_routes': {
            'tier_id': 'app_id',
        },
    }

    TYPES = {
        'applications': APPLICATION_DICT,
        'deployments': DEPLOYMENT_DICT,
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
        if not self.request.validated_params:
            self.results = self.model.all()
            return

        self.results = self.model.query().filter_by(
            **self.request.validated_params
        )

        if self.start is not None:
            self.results = self.results.filter(
                self.model.id >= self.start
            )

        if self.limit is not None:
            self.results = self.results.limit(self.limit)

    def validate_search_get(self, request):
        self.name = 'search'
        if self.request.matchdict['obj_type'] not in self.TYPES:
            self.request.errors.add(
                'path', 'obj_type',
                "Unknown object type {obj_type}. Supported object types are: "
                "{types}.".format(
                    obj_type=self.request.matchdict['obj_type'],
                    types=self.TYPES.keys(),
                )
            )
            self.request.errors.status = 404
            return

        self.obj_dict = self.TYPES[self.request.matchdict['obj_type']]
        self.model = self.obj_dict['model']
        self._validate_params(
            self.obj_dict['params'].keys() + ['limit', 'start']
        )

        for param in self.request.validated_params:
            if param not in self.obj_dict['params']:
                continue
            if self.obj_dict['params'][param] == 'choice':
                choice_param = '{param}_choices'.format(param=param)
                if choice_param in self.obj_dict:
                    setattr(self, choice_param, self.obj_dict[choice_param])
                else:
                    try:
                        if getattr(self.model, 'delegate', None):
                            table = self.model.delegate.__table__
                        else:
                            table = self.model.__table__
                        col_name = param
                        if param in self.obj_dict['param_routes']:
                            col_name = self.obj_dict['param_routes'][param]
                        setattr(self, choice_param,
                                table.columns[col_name].type.enums)
                    except Exception as exc:
                        raise tds.exception.ProgrammingError(
                            "No choices set for param {param}. "
                            "Got exception {e}.".format(param=param, e=exc)
                        )

        self._validate_json_params(self.obj_dict['params'])
        self._validate_json_params({'limit': 'integer', 'start': 'integer'})
        self.limit = self.start = None
        if 'limit' in self.request.validated_params:
            self.limit = self.request.validated_params.pop('limit')
        if 'start' in self.request.validated_params:
            self.start = self.request.validated_params.pop('start')
        self._route_params(self.obj_dict['param_routes'])
        self._get_results()

    @view(validators=('validate_search_get', 'validate_cookie'))
    def get(self):
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
            elif self.request.headers['Expect'] != 200:
                return self.make_response(
                    body='',
                    status="417 Expectation Failed",
                )
        return self.make_response([
            self.to_json_obj(x, self.obj_dict['param_routes']) for x in
            self.results
        ])

    @view(validators=('method_not_allowed'))
    def delete(self):
        return self.make_response({})

    @view(validators=('method_not_allowed'))
    def put(self):
        return self.make_response({})
