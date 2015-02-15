"""
REST API view for packages.
"""

from cornice.resource import resource, view

from . import utils

import tds.model


@resource(collection_path="/applications/{name_or_id}/packages",
          path="/applications/{name_or_id}/packages/{version}/{revision}")
class PackageView(object):
    """
    Package view. This object maps to the /applications/{name_or_id}/packages
    and /applications/{name_or_id}/packages/{version}/{revision} URLs.
    An object of this class is initalized to handle each request.
    The collection_* methods correspond to the /applications URL while the
    others correspond to the /applications/{name_or_id} URL.
    """

    def __init__(self, request):
        """
        Set params for this request.
        See method corresponding the HTTP method below for details on expected
        parameters.
        """
        self.request = request

    def validate_individual(self, request):
        """
        Validate that a package with the given name_or_id, version, and
        revision in the request URL exists and attach the package to the
        request at request.validated['package'].
        This validator can raise a "400 Bad Request" error.
        """
        utils.get_obj_by_name_or_id('application', request)
        if 'application' in request.validated:
            utils.get_pkg_by_version_revision(request)

    def validate_collection_get(self, request):
        """
        Get collection of packages matching given query parameters.
        Can raise "400 Bad Request" if unsupported params in query.
        """
        utils.get_obj_by_name_or_id('application', request)
        if 'application' in request.validated:
            utils.get_pkgs_by_limit_start(request)

    @view(validators=('validate_individual',))
    def delete(self):
        """
        Delete an individual package.
        """
        #TODO Implement the delete part.
        return utils.make_response(request.validated['package'])

    @view(validators=('validate_individual',))
    def get(self):
        """
        Return an individual package.
        """
        return utils.make_response(self.request.validated['package'])

    @view(validators=('validate_individual',))
    def put(self):
        """
        Update an existing package.
        """
        #TODO Implement this
        return utils.make_response({})

    @view(validators=('validate_collection_get',))
    def collection_get(self):
        """
        Return a list of matching packages for the query in the request.
        Request parameters:
            Request should either be empty (match all packages for the given
            application) or contain a 'limit' and 'start' parameters for
            pagination.
        Returns:
            "200 OK" if valid request successfully processed
        """
        return utils.make_response(self.request.validated['packages'])

    def collection_post(self):
        """
        Create a new package.
        """
        #TODO Implement this
        return utils.make_response([])
