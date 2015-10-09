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
from . import utils, types, descriptions


def init_view(_view_cls=None, name=None, plural=None, model=None,
              set_params=True):
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

    def real_decorator(cls, obj_name=name, obj_plural=plural, obj_model=model,
                       set_obj_params=set_params):
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

        if set_obj_params:
            json_types = getattr(
                types, "{name}_TYPES".format(
                    name=obj_name.upper().replace('-', '_')
                )
            )
            if 'user' in json_types:
                del json_types['user']
            if 'id' in json_types:
                del json_types['id']
            cls.types = json_types

            param_descripts = getattr(
                descriptions, "{name}_DESCRIPTIONS".format(
                    name=obj_name.upper().replace('-', '_')
                )
            )
            if 'user' in param_descripts:
                del param_descripts['user']
            if 'id' in param_descripts:
                del param_descripts['id']
            cls.param_descriptions = param_descripts

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
            raise tds.exceptions.ConfigurationError(
                "REST settings file does not exist. Expecting file {path}."
                .format(path=opj(os.path.dirname(os.path.realpath(__file__)),
                                 'settings.yml'))
            )
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
                            "Got exception {e}.".format(param=y, e=exc)
                        )

        super(BaseView, self).__init__(*args, **kwargs)

    def to_json_obj(self, obj, param_routes=None):
        """
        Return a JSON object representation of this object.
        """
        if param_routes is None:
            param_routes = self.param_routes

        d = obj
        if getattr(obj, 'to_dict', None) is not None:
            d = obj.to_dict()
        if not param_routes:
            return d

        for k in param_routes:
            if param_routes[k] in d:
                d[k] = d[param_routes[k]]
                del d[param_routes[k]]
        return d

    def get_obj_by_name_or_id(self, obj_type=None, model=None, name_attr=None,
                              param_name=None, can_be_name=True,
                              dict_name=None):
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
                model = self.model
        elif not model:
            model = getattr(tds.model, obj_type.title(), None)
            if model is None:
                raise tds.exceptions.NotFoundError('Model', [obj_type])

        if not param_name:
            param_name = 'name_or_id'

        try:
            obj_id = int(self.request.matchdict[param_name])
            obj = model.get(id=obj_id)
            name = False
        except ValueError:
            if can_be_name:
                obj_id = False
                name = self.request.matchdict[param_name]
                obj_dict = dict()
                if name_attr:
                    obj_dict[name_attr] = name
                elif 'name' in self.param_routes:
                    obj_dict[self.param_routes['name']] = name
                else:
                    obj_dict['name'] = name
                obj = model.get(**obj_dict)
            else:
                obj_id = self.request.matchdict[param_name]
                obj = None

        if obj is None:
            self.request.errors.add(
                'path', param_name,
                "{obj_type} with {prop} {val} does not exist.".format(
                    obj_type=obj_type.capitalize(),
                    prop="ID" if obj_id else "name",
                    val=obj_id if obj_id else name,
                )
            )
            self.request.errors.status = 404
        elif dict_name:
            self.request.validated[dict_name] = obj
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
        else:
            obj_cls = getattr(tds.model, obj_type.title(), None)

        if obj_cls is None:
            raise tds.exceptions.NotFoundError('Model', [obj_type])

        self._validate_params(('limit', 'start'))
        self._validate_json_params({'limit': 'integer', 'start': 'integer'})

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
        elif obj_cls == tds.model.AppTarget:
            self.request.validated[plural] = (
                self.request.validated[plural].filter(
                    obj_cls.app_type != '__dummy__'
                )
            )

        if 'limit' in self.request.validated_params:
            self.request.validated[plural] = (
                self.request.validated[plural].limit(
                    self.request.validated_params['limit']
                )
            )

    @staticmethod
    def make_response(body, status="200 OK", renderer="json", headers=None):
        """
        Make and return a Response with the given body and HTTP status code.
        """
        if headers is None:
            headers = dict()

        if renderer == "json":
            resp = Response(
                body=json.dumps(body, cls=TDSEncoder),
                content_type="text/json",
                status=status,
                headers=headers,
            )
            return resp
        else:
            raise NotImplementedError(
                "REST renderer not implemented: {r}.".format(
                    r=renderer,
                )
            )

    def _route_params(self, routes=None):
        """
        Map params from their front-end names to their backend names in the
        self.request.validated_params dictionary.
        """
        if routes is None:
            routes = self.param_routes
        for attr in routes:
            if attr in self.request.validated_params:
                self.request.validated_params[routes[attr]] = \
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
