"""
REST API view for packages.
"""

from cornice.resource import resource, view

import tds.model
from .base import BaseView, init_view


@resource(collection_path="/applications/{name_or_id}/packages",
          path="/applications/{name_or_id}/packages/{version}/{revision}")
@init_view(name='package')
class PackageView(BaseView):
    """
    Package view. This object maps to the /applications/{name_or_id}/packages
    and /applications/{name_or_id}/packages/{version}/{revision} URLs.
    An object of this class is initalized to handle each request.
    The collection_* methods correspond to the /applications URL while the
    others correspond to the /applications/{name_or_id} URL.
    """

    types = {
        'id': 'integer',
        'version': 'integer',
        'revision': 'integer',
        'status': 'choice',
        'builder': 'choice',
        'job': 'string',
    }

    param_routes = {
        'job': 'path'
    }

    defaults = {
        'status': 'pending',
    }

    required_post_fields = ('version', 'revision')

    permissions = {}

    def get_pkg_by_version_revision(self):
        """
        Validate that the package with the version, revision, and application
        in the request exists.
        Attach it at request.validated['package'] if it does.
        Attach an error with location='path', name='revision' and a
        description otherwise.
        This error with return a "400 Bad Request" response to this request.
        """
        try:
            version = int(self.request.matchdict['version'])
        except ValueError:
            self.request.errors.add(
                'path', 'version',
                'Version must be an integer'
            )
            return
        try:
            revision = int(self.request.matchdict['revision'])
        except ValueError:
            self.request.errors.add(
                'path', 'revision',
                'Revision must be an integer'
            )
            return
        try:
            pkg = tds.model.Package.get(
                application=self.request.validated['application'],
                version=self.request.matchdict['version'],
                revision=self.request.matchdict['revision'],
            )
        except KeyError:    # No request.validated['application'] entry
            raise tds.exceptions.TDSException(
                "No validated application when trying to locate package."
            )
        if pkg is None:
            self.request.errors.add(
                'path', 'revision',
                "Package with version {v} and revision {r} does"
                " not exist for this application.".format(
                    v=version,
                    r=revision,
                )
            )
            self.request.errors.status = 404
        else:
            self.request.validated['package'] = pkg

    def get_pkgs_by_limit_start(self):
        """
        Get all packages for the application request.validated['application'],
        optionally paginated by request.params['limit'] and
        request.params['start'] if those are non-null.
        """
        try:
            pkgs = tds.model.Package.query().filter(
                tds.model.Package.application == self.request.validated[
                    'application'
                ],
            ).order_by(tds.model.Package.id)
        except KeyError:    # No request.validated['application'] entry
            raise tds.exceptions.TDSException(
                "No validated application when trying to locate package."
            )
        else:
            self.request.validated['packages'] = pkgs
        self.get_collection_by_limit_start()

    def validate_package_put(self):
        """
        Validate a PUT request by preventing collisions over unique fields for
        packages.
        """
        self._validate_id("PUT")
        if 'version' in self.request.validated_params or 'revision' in \
                self.request.validated_params:
            found_pkg = self.model.get(
                application=self.request.validated['application'],
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
                    'version' if 'version' in self.request.validated_params
                        else 'revision',
                    "Unique constraint violated. Another package for this"
                    " application with this version and revision already"
                    " exists."
                )
                self.request.errors.status = 409

    def validate_package_post(self):
        """
        Validate a POST request by preventing collisions over unique fields.
        """
        self.get_obj_by_name_or_id('application')
        self._validate_id("POST")
        app_check = 'application' in self.request.validated
        ver_check = 'version' in self.request.validated_params
        rev_check = 'revision' in self.request.validated_params
        if not (app_check and ver_check and rev_check):
            return
        found_pkg = self.model.get(
            application=self.request.validated['application'],
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
        """
        Handle a POST request after the parameters are marked valid JSON.
        """
        self.request.validated_params['creator'] = self.request.validated[
            'user'
        ]
        return self._handle_collection_post()
