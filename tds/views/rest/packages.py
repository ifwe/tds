"""
REST API view for packages.
"""

from cornice.resource import resource

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
        'id': 'number',
        'version': 'number',
        'revision': 'number',
        'status': 'string',
        'builder': 'string',
    }

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

    def validate_pkg_put(self):
        """
        Validate a PUT request by preventing collisions over unique fields for
        packages.
        """
        self.validate_put_id()
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
