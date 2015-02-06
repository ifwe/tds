"""
REST API view for a project.
"""

from cornice.resource import resource, view

from .utils import make_response
import tds.model


@resource(collection_path="/projects", path="/projects/{name_or_id}")
class ProjectView(object):
    """
    Project view. This object maps to the /projects and /projects/{name_or_id}
    URL.
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
        If this is a POST request, validate that no project with the same name
        exists.
        Otherwise, validate that the project with given name exists and attach
        the project to the request at request.validated['project'].
        This validator will raise a "400 Bad Request" error.
        """
        try:
            proj_id = int(self.request.matchdict['name_or_id'])
            project = tds.model.Project.get(id=proj_id)
            name = False
        except ValueError:
            proj_id = False
            name = self.request.matchdict['name_or_id']
            project = tds.model.Project.get(name=name)
        if request.method == 'POST':
            if project is not None:
                request.errors.add(
                    'path', 'name',
                    "Project with {prop} {val} already exists".format(
                        prop="ID" if proj_id else "name",
                        val=proj_id if proj_id else name,
                    )
                )
        elif project is None:
            request.errors.add(
                'path', 'name',
                "Project with name {prop} {val} does not exist".format(
                    prop="ID" if proj_id else "name",
                    val=proj_id if proj_id else name,
                ),
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
        all_params = ('limit', 'start',) # for later: 'sort_by', 'reverse')
        for key in request.params:
            if key not in all_params:
                request.errors.add(
                    'query', key,
                    ("Unsupported query: {param}. Valid parameters: "
                     "{all_params}".format(param=key, all_params=all_params))
                )

        # This might be used later but isn't currently:
        # if 'sort_by' in request.params:
        #     valid_attrs = ('id', 'name')
        #     if request.params['sort_by'] not in valid_attrs:
        #         request.errors.add(
        #             'query', 'sort_by',
        #             ("Unsupported sort attribute: {val}. Valid attributes: "
        #              "{all_attrs}".format(
        #                 val=request.params['sort_by'],
        #                 all_attrs=valid_attrs,
        #              ))
        #         )
        #     elif request.params['sort_by'] == 'name':
        #         sort_by = tds.model.Project.name
        #     else:
        #         sort_by = tds.model.Project.id
        # request.validated['projects'].order_by(sort_by)

        if 'start' in request.params and request.params['start']:
            request.validated['projects'] = (
                tds.model.Project.query().order_by(tds.model.Project.id)
                    .filter(
                        tds.model.Project.id >= request.params['start']
                    )
            )
        else:
            request.validated['projects'] = (
                tds.model.Project.query()
                                 .order_by(tds.model.Project.id)
            )

        if 'limit' in request.params and request.params['limit']:
            request.validated['projects'] = (
                request.validated['projects'].limit(request.params['limit'])
            )

        # This code was designed to allow filtering on attributes.
        # It's preserved here for ideas in case it's relevant elsewhere.
        # names = set(request.params.getall('name'))
        # proj_ids = set(request.params.getall('id'))
        #
        # if proj_ids and names:
        #     request.validated['projects'] = tds.model.Project.query().filter(
        #         tds.model.Project.id.in_(tuple(proj_ids)),
        #         tds.model.Project.name.in_(tuple(names)),
        #     )
        # elif proj_ids:
        #     request.validated['projects'] = tds.model.Project.query().filter(
        #         tds.model.Project.id.in_(tuple(proj_ids)),
        #     )
        # elif names:
        #     request.validated['projects'] = tds.model.Project.query().filter(
        #         tds.model.Project.name.in_(tuple(names)),
        #     )
        # else:
        #     request.validated['projects'] = tds.model.Project.all()

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
