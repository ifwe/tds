"""
REST API view for applications.
"""

from cornice.resource import resource

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

    types = {
        'id': 'number',
        'name': 'string',
        'job_name': 'string',
        'build_host': 'string',
        'build_type': 'string',
        'deploy_type': 'string',
        'arch': 'string',
    }
