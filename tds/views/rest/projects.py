"""
REST API view for a project.
"""

from cornice.resource import resource, view

from .utils import make_response
import tds.model


@resource(collection_path="/projects", path="/projects/{name}")
class ProjectView(object):
    """
    Project view. This object maps to the /projects and /projects/{name} URL.
    An object of this class is initalized to handle each request.
    The collection_* methods correspond to the /projects URL while the others
    correspond to the /projects/{name} URL.
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
        If this is a POST request, validate that no project with the same name
        exists.
        Otherwise, validate that the project with given name exists and attach
        the project to the request at request.validated['project'].
        This validator will raise a "400 Bad Request" error.
        """
        name = self.request.matchdict['name']
        project = tds.model.Project.get(name=name)
        if request.method == 'POST':
            if project is not None:
                request.errors.add(
                    'path', 'name',
                    "Project with name {name} already exists".format(
                        name=name
                    )
                )
        elif project is None:
            request.errors.add(
                'path', 'name',
                "Project with name {name} does not exist".format(name=name)
            )
        else:
            request.validated['project'] = project

    def validate_collection_get(self, request):
        """
        Make sure that the selection parameters are valid for projects.
        If they are not, raise "400 Bad Request".
        Else, set request.validated['projects'] to projects matching select
        query.
        """
        if 'names' in request.params:
            names = set(request.params.pop('name'))
        else:
            names = set()

        if 'ids' in request.params:
            proj_ids = set(request.params.pop('id'))
        else:
            proj_ids = set()

        if 'name' in request.params:
            names.add(request.params.pop('name'))
        if 'id' in request.params:
            proj_ids.add(request.params.pop('id'))

        if request.params:
            for key in request.params:
                request.errors.add(
                    'query', key, "Unknown project attribute {attr}".format(
                        attr=key,
                    )
                )

        if proj_ids and names:
            request.validated['projects'] = tds.model.Project.find(
                project_id.in_(proj_ids),
                name.in_(names),
            )
        elif proj_ids:
            request.validated['projects'] = tds.model.Project.find(
                project_id.in_(proj_ids),
            )
        elif names:
            request.validated['projects'] = tds.model.Project.find(
                name.in_(names),
            )
        else:
            request.validated['projects'] = tds.model.Project.all()

    @view(validators=('validate_individual',))
    def delete(self):
        """
        Delete an individual project.
        """
        #TODO Implement the delete part.
        return make_response(request.validated['project'])

    @view(validators=('validate_individual',))
    def get(self):
        """
        Return an individual project.
        """
        return make_response(self.request.validated['project'])

    @view(validators=('validate_individual',))
    def post(self):
        """
        Create a new project.
        """
        #TODO Implement this
        return make_response({})

    @view(validators=('validate_individual',))
    def put(self):
        """
        Update an existing project.
        """
        #TODO Implement this
        return make_response({})

    def collection_delete(self):
        """
        Delete all matching projects. Admin access required.
        """
        #TODO Implement this
        return make_response([])

    @view(validators=('validate_collection_get',))
    def collection_get(self):
        """
        Return a list of matching projects for the query in the request.
        Parameters:
            Request should either be empty (match all projects) or contain
            a dictionary of attributes to match against projects.
        Returns:
            "200 OK" if valid request successfully processed
        """
        return make_response(self.request.validated['projects'])

    def collection_post(self):
        """
        Create new projects with given params.
        """
        #TODO Implement this
        return make_response([])

    def collection_put(self):
        """
        Update matching projects with given new params.
        """
        #TODO Implement this
        return make_response([])
