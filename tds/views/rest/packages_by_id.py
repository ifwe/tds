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
        'name': 'string',
    }

    param_routes = {
        'job': 'path',
        'name': 'pkg_name',
    }

    defaults = {
        'status': 'pending',
    }

    required_post_fields = ('version', 'revision', 'name')

    def validate_individual_package_by_id(self, request):
        self.get_obj_by_name_or_id(obj_type='Package', model=self.model,
                                   param_name='id', can_be_name=False,
                                   dict_name=self.name)

    def validate_package_by_id_put(self):
        self._validate_id("PUT", "package")

        if any(x in self.request.validated_params for x in
               ('version', 'revision', 'name')):
            found_pkg = self.model.get(
                application=tds.model.Application.get(
                    pkg_name=self.request.validated_params['name']
                ) if 'name' in self.request.validated_params else
                    self.request.validated[self.name].application,
                version=self.request.validated_params['version'] if 'version'
                    in self.request.validated_params else
                    self.request.validated[self.name].version,
                revision=self.request.validated_params['revision'] if
                    'revision' in self.request.validated_params else
                    self.request.validated[self.name].revision,
            )
            if found_pkg and found_pkg != self.request.validated[self.name]:
                self.request.errors.add(
                    'query',
                    'name' if 'name' in self.request.validated_params
                        else 'version' if 'version' in
                        self.request.validated_params else 'revision',
                    "Unique constraint violated. Another package for this"
                    " application with this version and revision already"
                    " exists."
                )
                self.request.errors.status = 409

    def validate_package_by_id_post(self):
        self._validate_id("POST", "package")
        if 'name' not in self.request.validated_params:
            return
        found_app = tds.model.Application.get(
            pkg_name=self.request.validated_params['name']
        )
        ver_check = 'version' in self.request.validated_params
        rev_check = 'revision' in self.request.validated_params
        if not found_app:
            self.request.errors.add(
                'query', 'name',
                "Application with name {name} does not exist.".format(
                    name=self.request.validated_params['name']
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
                      'validate_obj_post', 'validate_cookie'))
    def collection_post(self):
        self.request.validated_params['creator'] = self.request.validated[
            'user'
        ]
        return self._handle_collection_post()
