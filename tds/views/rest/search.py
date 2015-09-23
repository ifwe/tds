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
        'application': APPLICATION_DICT,
        'deployment': DEPLOYMENT_DICT,
        'ganglia': GANGLIA_DICT,
        'hipchat': HIPCHAT_DICT,
        'host': HOST_DICT,
        'host_deployment': HOST_DEPLOYMENT_DICT,
        'package': PACKAGE_DICT,
        'project': PROJECT_DICT,
        'tier': TIER_DICT,
        'tier_deployment': TIER_DEPLOYMENT_DICT,
    }

    def validate_search_get(self, request):
        pass

    @view(validators=('validate_search_get', 'validate_cookie'))
    def get(self):
        return self.make_response(self.plural)

    @view(validators=('method_not_allowed'))
    def post(self):
        return self.make_response({})

    @view(validators=('method_not_allowed'))
    def put(self):
        return self.make_response({})
