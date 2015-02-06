"""
REST API view for applications.
"""

from cornice.resource import resource, view

from . import utils

import tds.model


@resource(collection_path="/applications", path="/applications/{name_or_id}")
class ApplicationView(object):
    """
    Application view. This object maps to the /applications and
    /applications/{name_or_id} URL.
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
        Validate that an application with the given name_or_id in the request
        URL exists and attach the application to the request at
        request.validated['application'].
        This validator can raise a "400 Bad Request" error.
        """
        utils.get_obj_by_name_or_id('application', request)

    def validate_collection_get(self, request):
        """
        Get collection of applications matching given query parameters.
        Can raise "400 Bad Request" if unsupported params in query.
        """
        utils.get_collection_by_limit_start('application', request)

    @view(validators=('validate_individual',))
    def delete(self):
        """
        Delete an individual project.
        """
        #TODO Implement the delete part.
        return utils.make_response(request.validated['application'])

    @view(validators=('validate_individual',))
    def get(self):
        """
        Return an individual application.
        """
        return utils.make_response(self.request.validated['application'])

    @view(validators=('validate_individual',))
    def put(self):
        """
        Update an existing application.
        """
        #TODO Implement this
        return utils.make_response({})

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
        return utils.make_response(self.request.validated['applications'])

    def collection_post(self):
        """
        Create a new application
        """
        #TODO Implement this
        return utils.make_response([])
