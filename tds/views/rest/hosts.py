"""
REST API view for hosts.
"""

from cornice.resource import resource, view

import tds

from . import utils
from .base import BaseView, init_view

@resource(collection_path="/hosts", path="/hosts/{name_or_id}")
@init_view(name='host', model=tds.model.HostTarget)
class HostView(BaseView):
    """
    Application view. This object maps to the /hosts and
    /hosts/{name_or_id} URLs.
    An object of this class is initalized to handle each request.
    The collection_* methods correspond to the /hosts URL while the
    others correspond to the /hosts/{name_or_id} URL.
    """

    # JSON types for params.
    types = {
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
    }

    # Remove these choice fields when they are defined in TagOpsDB.
    arch_choices = ('i386', 'noarch', 'x86_64',)

    distribution_choices = (
        'centos5.4', 'centos6.2', 'centos6.4', 'centos6.5',
        'centos7.0', 'centos7.1', 'fedora18', 'rhel5.3', 'rhel6.2',
        'rhel6.3', 'rhel6.4', 'rhel6.5', 'ontap',
    )

    # URL parameter routes to Python object fields.
    # Params not included are mapped to themselves.
    param_routes = {
        'name': 'hostname',
        'cage': 'cage_location',
        'cab': 'cab_location',
        'rack': 'rack_location',
        'tier_id': 'app_id',
    }

    defaults = {
        'state': 'operational',
    }

    required_post_fields = ("name", "tier_id")

    permissions = {
        'put': 'admin',
        'delete': 'admin',
        'collection_post': 'admin',
    }

    def validate_host_post(self):
        """
        Validate a POST request by preventing collisions over unique fields and
        validating that an app tier with the given tier_id exists.
        """
        self._validate_id("POST")
        self._validate_name("POST")
        self._validate_foreign_key('tier_id', 'app tier', tds.model.AppTarget)

    def validate_host_put(self):
        """
        Validate a PUT request by preventing collisions over unique fields and
        validating that an app tier with the given tier_id exists.
        """
        self._validate_id("PUT")
        self._validate_name("PUT")
        self._validate_foreign_key('tier_id', 'app tier', tds.model.AppTarget)
