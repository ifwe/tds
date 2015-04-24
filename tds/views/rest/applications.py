"""
REST API view for applications.
"""

from cornice.resource import resource, view

import tagopsdb

from .base import BaseView, init_view


@resource(collection_path="/applications", path="/applications/{name_or_id}")
@init_view(name='application')
class ApplicationView(BaseView):
    """
    Application view. This object maps to the /applications and
    /applications/{name_or_id} URLs.
    An object of this class is initalized to handle each request.
    The collection_* methods correspond to the /applications URL while the
    others correspond to the /applications/{name_or_id} URL.
    """

    # JSON types for params.
    types = {
        'id': 'number',
        'name': 'string',
        'job': 'string',
        'build_host': 'string',
        'build_type': 'string',
        'deploy_type': 'string',
        'arch': 'string',
        'validation_type': 'string',
        'env_specific': 'boolean',
    }

    # URL parameter routes to Python object fields.
    # Params not included are mapped to themselves.
    param_routes = {
        'name': 'pkg_name',
        'job': 'job_name',
    }
