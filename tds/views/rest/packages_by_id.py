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
        'revision': 'integer',
        'status': 'choice',
        'builder': 'choice',
        'job': 'string',
        'app_name': 'string',
    }

    param_routes = {
        'job': 'path',
        'app_name': 'name',
    }

    defaults = {
        'status': 'pending',
    }

    required_post_fields = ('version', 'revision', 'app_name')

    def validate_package_by_id_put(self):
        self._validate_id("PUT", "package")

        if 'version' in self.request.validated_params or 'revision' in \
                self.request.validated_params:
            found_pkg = self.model.get(
                # application=
            )

    def validate_package_by_id_post(self):
        self._validate_id("POST", "package")
        if 'app_name' not in self.request.validated_params:
            return
        found_app = tds.model.Application.get(
            pkg_name=self.request.validated_params['app_name']
        )
        ver_check = 'version' in self.request.validated_params
        rev_check = 'revision' in self.request.validated_params
        if not found_app:
            self.request.errors.add(
                'query', 'app_name',
                "Application with name {name} does not exist.".format(
                    name=self.request.validated_params['app_name']
                )
            )
            self.request.status = 400
            return
        elif not (ver_check and rev_check):
            return
        else:
            self.request.validated_params['application'] = found_app
        found_pkg = self.model.get(
            application=found_app,
            version=self.request.validated_params['version'],
            revision=self.request.validated_params['revision'],
        )
        if found_pkg:
            self.request.errors.add(
                'query', 'version',
                "Unique constraint violated. A package for this application"
                " with this version and revision already exists."
            )
            self.request.errors.status = 409

    @view(validators=('validate_put_post', 'validate_post_required',
                      'validate_cookie'))
    def collection_post(self):
        self.request.validated_params['creator'] = self.request.validated[
            'user'
        ]
        return self._handle_collection_post()
