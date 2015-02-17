"""
REST API view for applications.
"""

from cornice.resource import resource, view

from .base import BaseView


@resource(collection_path="/applications", path="/applications/{name_or_id}")
class ApplicationView(BaseView):
    """
    Application view. This object maps to the /applications and
    /applications/{name_or_id} URLs.
    An object of this class is initalized to handle each request.
    The collection_* methods correspond to the /applications URL while the
    others correspond to the /applications/{name_or_id} URL.
    """

    @view(validators=('validate_individual',))
    def delete(self):
        """
        Delete an individual application.
        """
        #TODO Implement the delete part.
        return self.make_response(request.validated['application'])

    @view(validators=('validate_individual',))
    def get(self):
        """
        Return an individual application.
        """
        return self.make_response(self.request.validated['application'])

    @view(validators=('validate_individual',))
    def put(self):
        """
        Update an existing application.
        """
        #TODO Implement this
        return self.make_response({})

    @view(validators=('validate_collection_get',))
    def collection_get(self):
        """
        Return a list of matching applications for the query in the request.
        Request parameters:
            Request should either be empty (match all applications) or contain
            a 'limit' and 'start' parameters for pagination.
        Returns:
            "200 OK" if valid request successfully processed
        """
        return self.make_response(self.request.validated['applications'])

    def collection_post(self):
        """
        Create a new application
        """
        #TODO Implement this
        return self.make_response([])
