"""
Base view class for REST API.
"""

import os
import json
import yaml

from os.path import join as opj

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
        try:
            with open(opj(os.path.dirname(os.path.realpath(__file__)),
                          'settings.yml')) as f:
                self.settings = yaml.load(f.read())
        except:
            pass
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
            if attr in self.request.validated_params:
                self.request.validated_params[self.param_routes[attr]] = \
                    self.request.validated_params[attr]
                del self.request.validated_params[attr]
        if self.name == 'package':
            self.request.validated_params['application'] = \
                self.request.validated['application']
            self.request.validated_params['pkg_name'] = \
                self.request.validated['application'].name

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
