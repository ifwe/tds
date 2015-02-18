"""
Base view class for REST API.
"""

import json

from pyramid.response import Response
from cornice.resource import view

from ..json_encoder import TDSEncoder

import tds.model


class BaseView(object):
    """
    This class manages & enforces permission and does basic initialization of
    views. It also handles validation for certain things.
    """

    #TODO: Add permissions system

    def __init__(self, request):
        """
        Set params for this request.
        See method corresponding the HTTP method below for details on expected
        parameters.
        """
        self.request = request

    @staticmethod
    def make_response(body, status="200 OK", renderer="json"):
        """
        Make and return a Response with the given body and HTTP status code.
        """
        if renderer == "json":
            return Response(
                body=json.dumps(body, cls=TDSEncoder),
                content_type="text/json",
                status=status,
            )
        else:
            raise NotImplementedError(
                "REST renderer not implemented: {r}.".format(
                    r=renderer,
                )
            )

    def validate_individual(self, request):
        """
        Validate that the project with given name exists and attach
        the project to the request at request.validated['project'].
        This validator can raise a "400 Bad Request" error.
        """
        if self.name == 'package':
            self.get_obj_by_name_or_id('application')
            if 'application' in request.validated:
                self.get_pkg_by_version_revision()
        else:
            self.get_obj_by_name_or_id()

    def validate_collection_get(self, request):
        """
        Make sure that the selection parameters are valid for projects.
        If they are not, raise "400 Bad Request".
        Else, set request.validated['projects'] to projects matching query.
        """
        if self.name == 'package':
            self.get_obj_by_name_or_id('application')
            if 'application' in request.validated:
                self.get_pkgs_by_limit_start()
        else:
            self.get_collection_by_limit_start()

    @view(validators=('validate_individual',))
    def get(self):
        """
        Return an individual package.
        """
        return self.make_response(self.request.validated[self.name])

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
        return self.make_response(self.request.validated[self.plural])

    @view(validators=('validate_individual',))
    def delete(self):
        """
        Delete an individual package.
        """
        #TODO Implement the delete part.
        return self.make_response(self.request.validated[self.name])

    @view(validators=('validate_individual',))
    def put(self):
        """
        Update an existing package.
        """
        #TODO Implement this
        return self.make_response(self.request.validated[self.name])

    def collection_post(self):
        """
        Create a new package.
        """
        #TODO Implement this
        return self.make_response(self.request.validated[self.plural])

    def get_obj_by_name_or_id(self, obj_type=None):
        """
        Validate that an object of type self.name with the name_or_id given in
        the request exists and attach it to the request at
        request.validated[obj_type].
        Otherwise, attach an error with location='path', name='name_or_id' and
        a description.
        This error will return a "400 Bad Request" response to this request.
        """
        if not obj_type:
            obj_type = self.name
            if getattr(self, 'model', None):
                obj_cls = self.model
        else:
            obj_cls = getattr(tds.model, obj_type.title(), None)
            if obj_cls is None:
                raise tds.exceptions.NotFoundError('Model', [obj_type])

        try:
            obj_id = int(self.request.matchdict['name_or_id'])
            obj = obj_cls.get(id=obj_id)
            name = False
        except ValueError:
            obj_id = False
            name = self.request.matchdict['name_or_id']
            obj = obj_cls.get(name=name)

        if obj is None:
            self.request.errors.add(
                'path', 'name_or_id',
                "{obj_type} with {prop} {val} does not exist.".format(
                    obj_type=obj_type.title(),
                    prop="ID" if obj_id else "name",
                    val=obj_id if obj_id else name,
                )
            )
            self.request.errors.status = 404
        else:
            self.request.validated[obj_type] = obj

    def get_collection_by_limit_start(self, obj_type=None, plural=None):
        """
        Make sure that the selection parameters are valid for collection GET.
        If they are not, raise "400 Bad Request".
        Else, set request.validated[plural] to objects matching query.
        If obj_type is not provided, it is defaulted to self.name.
        If plural is not provided, it is defaulted to obj_type + 's' if
        obj_type is provided and to self.plural if obj_type is not provided.
        """
        if not plural and not obj_type:
            plural = self.plural
        elif obj_type:
            plural = obj_type + 's'

        if not obj_type:
            obj_type = self.name
            if getattr(self, 'model', None):
                obj_cls = self.model


        obj_cls = getattr(tds.model, obj_type.title(), None)
        if obj_cls is None:
            raise tds.exceptions.NotFoundError('Model', [obj_type])

        all_params = ('limit', 'start',) # for later: 'sort_by', 'reverse')
        for key in self.request.params:
            if key not in all_params:
                self.request.errors.add(
                    'query', key,
                    ("Unsupported query: {param}. Valid parameters: "
                     "{all_params}.".format(param=key, all_params=all_params))
                )

        # This might be used later but isn't currently:
        # if 'sort_by' in self.request.params:
        #     valid_attrs = ('id', 'name')
        #     if self.request.params['sort_by'] not in valid_attrs:
        #         self.request.errors.add(
        #             'query', 'sort_by',
        #             ("Unsupported sort attribute: {val}. Valid attributes: "
        #              "{all_attrs}".format(
        #                 val=self.request.params['sort_by'],
        #                 all_attrs=valid_attrs,
        #              ))
        #         )
        #     elif self.request.params['sort_by'] == 'name':
        #         sort_by = tds.model.Project.name
        #     else:
        #         sort_by = tds.model.Project.id
        # self.request.validated['projects'].order_by(sort_by)

        if plural not in self.request.validated:
            self.request.validated[plural] = obj_cls.query().order_by(
                obj_cls.id
            )

        if 'start' in self.request.params and self.request.params['start']:
            self.request.validated[plural] = (
                self.request.validated[plural].filter(
                    obj_cls.id>=self.request.params['start']
                )
            )

        if obj_cls == tds.model.Application:
            self.request.validated[plural] = (
                self.request.validated[plural].filter(
                    obj_cls.pkg_name!='__dummy__'
                )
            )

        if 'limit' in self.request.params and self.request.params['limit']:
            self.request.validated[plural] = (
                self.request.validated[plural].limit(
                    self.request.params['limit']
                )
            )

        # This code was designed to allow filtering on attributes.
        # It's preserved here for ideas in case it's relevant elsewhere.
        # names = set(self.request.params.getall('name'))
        # proj_ids = set(self.request.params.getall('id'))
        #
        # if proj_ids and names:
        #     self.request.validated['projects'] = tds.model.Project.query().filter(
        #         tds.model.Project.id.in_(tuple(proj_ids)),
        #         tds.model.Project.name.in_(tuple(names)),
        #     )
        # elif proj_ids:
        #     self.request.validated['projects'] = tds.model.Project.query().filter(
        #         tds.model.Project.id.in_(tuple(proj_ids)),
        #     )
        # elif names:
        #     self.request.validated['projects'] = tds.model.Project.query().filter(
        #         tds.model.Project.name.in_(tuple(names)),
        #     )
        # else:
        #     self.request.validated['projects'] = tds.model.Project.all()
