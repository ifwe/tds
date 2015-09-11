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
from . import utils


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
        if self.valid_attrs and len(self.types) > 0:
            for y in [x for x in self.types if self.types[x] == 'choice']:
                choices = getattr(
                    self, '{param}_choices'.format(param=y), None
                )
                if choices is None or len(choices) == 0:
                    try:
                        if getattr(self.model, 'delegate', None):
                            table = self.model.delegate.__table__
                        else:
                            table = self.model.__table__
                        col_name = y
                        if y in self.param_routes:
                            col_name = self.param_routes[y]
                        setattr(
                            self,
                            '{param}_choices'.format(param=y),
                            table.columns[col_name].type.enums
                        )
                    except Exception as exc:
                        raise tds.exceptions.ProgrammingError(
                            "No choices set for param {param}. "
                            "Got exception {e}".format(param=y, e=exc)
                        )

        super(BaseView, self).__init__(*args, **kwargs)

    def to_json_obj(self, obj):
        """
        Return a JSON object representation of this object.
        """
        d = obj.to_dict()
        if not self.param_routes:
            return d

        for k in self.param_routes:
            if self.param_routes[k] in d:
                d[k] = d[self.param_routes[k]]
                del d[self.param_routes[k]]
        return d

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

    @view(validators=('validate_collection_get', 'validate_cookie'))
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
        return self.make_response(
            [self.to_json_obj(x) for x in self.request.validated[self.plural]]
        )

    def _handle_collection_post(self):
        """
        Handle the addition and commit of the model in a POST request after
        all validation has been completed.
        Create and return the HTTP response.
        """
        self._route_params()
        if getattr(self.model, 'create', None):
            self.request.validated[self.name] = self.model.create(
                **self.request.validated_params
            )
        else:
            self.request.validated[self.name] = self.model.update_or_create(
                self.request.validated_params
            )
            tagopsdb.Session.commit()
        return self.make_response(
            self.to_json_obj(self.request.validated[self.name]),
            "201 Created",
        )

    @view(validators=('validate_put_post', 'validate_post_required',
                      'validate_obj_post', 'validate_cookie'))
    def collection_post(self):
        """
        Handle a POST request after the parameters are marked valid JSON.
        """
        return self._handle_collection_post()

    @view(validators=('validate_individual', 'validate_obj_delete',
                      'validate_cookie'))
    def delete(self):
        """
        Delete an individual resource.
        """
        if 'delete_cascade' in self.request.validated:
            for obj in self.request.validated['delete_cascade']:
                tagopsdb.Session.delete(obj)
            tagopsdb.Session.commit()
        tagopsdb.Session.delete(self.request.validated[self.name])
        tagopsdb.Session.commit()
        return self.make_response(
            self.to_json_obj(self.request.validated[self.name])
        )

    @view(validators=('validate_individual', 'validate_cookie'))
    def get(self):
        """
        Return an individual resource.
        """
        return self.make_response(
            self.to_json_obj(self.request.validated[self.name])
        )

    @view(validators=('validate_individual', 'validate_put_post',
                      'validate_obj_put', 'validate_cookie'))
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
        return self.make_response(
            self.to_json_obj(self.request.validated[self.name])
        )
