"""
REST API view for projects.
"""

from cornice.resource import resource, view

from .base import BaseView


@resource(collection_path="/projects", path="/projects/{name_or_id}")
class ProjectView(BaseView):
    """
    Project view. This object maps to the /projects and /projects/{name_or_id}
    URLs.
    An object of this class is initalized to handle each request.
    The collection_* methods correspond to the /projects URL while the others
    correspond to the /projects/{name_or_id} URL.
    """

    @view(validators=('validate_individual',))
    def delete(self):
        """
        Delete an individual project.
        """
        #TODO Implement the delete part.
        return self.make_response(request.validated['project'])

    @view(validators=('validate_individual',))
    def get(self):
        """
        Return an individual project.
        """
        return self.make_response(self.request.validated['project'])

    @view(validators=('validate_individual',))
    def put(self):
        """
        Update an existing project.
        """
        #TODO Implement this
        return self.make_response({})

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
        return self.make_response(self.request.validated['projects'])

    def collection_post(self):
        """
        Create a new project with given params.
        """
        #TODO Implement this
        return self.make_response([])
