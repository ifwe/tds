"""
REST API view for packages retrieved by ID.
"""

from cornice.resource import resource, view

import tds.model
from .base import BaseView, init_view

@resource(collection_path="/packages", path="/packages/{id}")
@init_view(name='package-by-id', model=tds.model.Package)
class PackageByIDView(BaseView):

    types = {
        'id': 'integer',
        'version': 'integer',
        'status': 'choice',
        'builder': 'choice',
        'job': 'string',
        'name': 'string',
    }

    param_routes = {
        'job': 'path',
    }

    defaults = {
        'status': 'pending',
    }

    required_post_fieds = ('version', 'revision', 'name')

    @view(validators=('validate_put_post', 'validate_post_required',
                      'validate_cookie'))
    def collection_post(self):
        self.request.validated_params['creator'] = self.request.validated[
            'user'
        ]
        return self._handle_collection_post()
