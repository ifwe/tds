"""
REST API view for packages.
"""

from cornice.resource import resource, view

from .base import BaseView


@resource(collection_path="/applications/{name_or_id}/packages",
          path="/applications/{name_or_id}/packages/{version}/{revision}")
class PackageView(BaseView):
    """
    Package view. This object maps to the /applications/{name_or_id}/packages
    and /applications/{name_or_id}/packages/{version}/{revision} URLs.
    An object of this class is initalized to handle each request.
    The collection_* methods correspond to the /applications URL while the
    others correspond to the /applications/{name_or_id} URL.
    """

    @view(validators=('validate_individual',))
    def delete(self):
        """
        Delete an individual package.
        """
        #TODO Implement the delete part.
        return self.make_response(request.validated['package'])

    @view(validators=('validate_individual',))
    def get(self):
        """
        Return an individual package.
        """
        return self.make_response(self.request.validated['package'])

    @view(validators=('validate_individual',))
    def put(self):
        """
        Update an existing package.
        """
        #TODO Implement this
        return self.make_response({})

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
        return self.make_response(self.request.validated['packages'])

    def collection_post(self):
        """
        Create a new package.
        """
        #TODO Implement this
        return self.make_response([])
