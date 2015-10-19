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

    # URL parameter routes to Python object fields.
    # Params not included are mapped to themselves.
    param_routes = {
        'name': 'pkg_name',
        'job': 'path',
    }

    individual_allowed_methods = dict(
        GET=dict(description="Get application matching name or ID."),
        PUT=dict(description="Update application matching name or ID."),
    )

    collection_allowed_methods = dict(
        GET=dict(description="Get a list of applications, optionally by limit "
                 "and/or start"),
        POST=dict(description="Add a new application"),
    )

    defaults = {
        'arch': 'noarch',
        'build_type': 'jenkins',
        'build_host': 'build_host',
        'deploy_type': 'rpm',
        'validation_type': 'matching',
    }

    required_post_fields = ("name", "job")

    permissions = {
        'put': 'admin',
        'delete': 'admin',
        'collection_post': 'admin',
    }
