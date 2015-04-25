"""
Base view class for REST API.
"""

import json

from pyramid.response import Response
from cornice.resource import view

from ..json_encoder import TDSEncoder

import tagopsdb

import tds.model
import tds.exceptions

from .validators import ValidatedView


def init_view(_view_cls=None, name=None, plural=None, model=None):
    """
    This is a decorator that will fill in some basic information for a class
    based on the information provided.
    For most views, just the name will be sufficient and is always required,
    but each attribute set on the view class can be overridden by providing it
    explicitly to this decorator.
    The _view_cls is the child of BaseView below.
    The attributes are directly added to the view class
    (name -> _view_cls.name).
    """

    def real_decorator(cls, obj_name=name, obj_plural=plural, obj_model=model):
        """
        Do the usual function-in-function decorator thing.
        """
        if not obj_name:
            raise tds.exceptions.ProgrammingError(
                "No name provided for decorator."
            )
        cls.name = obj_name

        if obj_plural is None:
            obj_plural = cls.name + 's'
        cls.plural = obj_plural

        if obj_model is None:
            obj_model = getattr(tds.model, cls.name.title(), None)
        if obj_model is None:
            raise tds.exceptions.ProgrammingError(
                "No model named {name}.".format(name=cls.name.title())
            )
        cls.model = obj_model

        return cls
    return real_decorator


class BaseView(ValidatedView):
    """
    This class manages & enforces permission, does basic view initialization.
    It also handles validation for requests and parameters in requests.
    """

    #TODO: Add permissions system

    def __init__(self, request, *args, **kwargs):
        """
        Set params for this request.
        See method corresponding the HTTP method below for details on expected
        parameters.
        """
        self.request = request
        if getattr(self, 'types', None):
            self.valid_attrs = self.types.keys()
        else:
            self.valid_attrs = []
        if not getattr(self, 'required_post_fields', None):
            self.required_post_fields = tuple()
        if not getattr(self, 'param_routes', None):
            self.param_routes = {}
        if not getattr(self, 'defaults', None):
            self.defaults = {}
        super(BaseView, self).__init__(*args, **kwargs)

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

    def _route_params(self):
        """
        Map params from their front-end names to their backend names in the
        self.request.validated_params dictionary.
        """
        for attr in self.param_routes:
            self.request.validated_params[self.param_routes[attr]] = \
                self.request.validated_params[attr]
            del self.request.validated_params[attr]

    def _handle_collection_post(self):
        """
        Handle the addition and commit of the model in a POST request after
        all validation has been completed.
        Create and return the HTTP response.
        """
        self._route_params()
        self.request.validated[self.name] = self.model.create(
            **self.request.validated_params
        )
        return self.make_response(self.request.validated[self.name],
                                  "201 Created")

    @view(validators=('validate_individual',))
    def get(self):
        """
        Return an individual resource.
        """
        return self.make_response(self.request.validated[self.name])

    @view(validators=('validate_collection_get',))
    def collection_get(self):
        """
        Return a list of matching resources for the query in the request.
        Request parameters:
            Request should either be empty (match all packages for the given
            application) or contain a 'limit' and 'start' parameters for
            pagination.
        Returns:
            "200 OK" if valid request successfully processed
        """
        return self.make_response(self.request.validated[self.plural])

    @view(validators=('validate_individual', 'validate_put_post',
                      'validate_obj_put'))
    def put(self):
        """
        Handle a PUT request after the parameters are marked valid JSON.
        """
        for attr in self.request.validated_params:
            setattr(
                self.request.validated[self.name],
                self.param_routes[attr] if attr in self.param_routes else attr,
                self.request.validated_params[attr],
            )
        tagopsdb.Session.commit()
        return self.make_response(self.request.validated[self.name])

    @view(validators=('validate_individual',))
    def delete(self):
        """
        Delete an individual resource.
        """
        #TODO Implement the delete part.
        return self.make_response(self.request.validated[self.name])

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

        self._validate_params(('limit', 'start'))

        if plural not in self.request.validated:
            self.request.validated[plural] = obj_cls.query().order_by(
                obj_cls.id
            )

        if 'start' in self.request.validated_params:
            self.request.validated[plural] = (
                self.request.validated[plural].filter(
                    obj_cls.id >= self.request.validated_params['start']
                )
            )

        if obj_cls == tds.model.Application:
            self.request.validated[plural] = (
                self.request.validated[plural].filter(
                    obj_cls.pkg_name != '__dummy__'
                )
            )

        if 'limit' in self.request.validated_params:
            self.request.validated[plural] = (
                self.request.validated[plural].limit(
                    self.request.validated_params['limit']
                )
            )
