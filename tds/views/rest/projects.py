"""
REST API view for projects.
"""

from cornice.resource import resource, view

from . import utils

import tds.model


@resource(collection_path="/projects", path="/projects/{name_or_id}")
class ProjectView(object):
    """
    Project view. This object maps to the /projects and /projects/{name_or_id}
    URLs.
    An object of this class is initalized to handle each request.
    The collection_* methods correspond to the /projects URL while the others
    correspond to the /projects/{name_or_id} URL.
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
        Validate that the project with given name exists and attach
        the project to the request at request.validated['project'].
        This validator can raise a "400 Bad Request" error.
        """
        utils.get_obj_by_name_or_id('project', request)

    def validate_collection_get(self, request):
        """
        Make sure that the selection parameters are valid for projects.
        If they are not, raise "400 Bad Request".
        Else, set request.validated['projects'] to projects matching query.
        """
        utils.get_collection_by_limit_start('project', request)

    @view(validators=('validate_individual',))
    def delete(self):
        """
        Delete an individual project.
        """
        #TODO Implement the delete part.
        return utils.make_response(request.validated['project'])

    @view(validators=('validate_individual',))
    def get(self):
        """
        Return an individual project.
        """
        return utils.make_response(self.request.validated['project'])

    @view(validators=('validate_individual',))
    def put(self):
        """
        Update an existing project.
        """
        #TODO Implement this
        return utils.make_response({})

    @view(validators=('validate_collection_get',))
    def collection_get(self):
        """
        Return a list of matching projects for the query in the request.
        Request parameters:
            Request should either be empty (match all projects) or contain
            a 'limit' and 'start' parameters for pagination.
        Returns:
            "200 OK" if valid request successfully processed
        """
        return utils.make_response(self.request.validated['projects'])

    def collection_post(self):
        """
        Create a new project with given params.
        """
        #TODO Implement this
        return utils.make_response([])
