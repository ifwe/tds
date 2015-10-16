"""
A view with validations of parameters given in request queries.
This class is separated out for separation of function.
Its only intended use is as a base class for the BaseView; directly importing
and using this view is discouraged.
"""

import datetime

import tds, tagopsdb

from . import utils
from .json_validators import JSONValidatedView


class ValidatedView(JSONValidatedView):
    """
    This class implements common non-JSON validators.
    """

    def _validate_params(self, valid_params):
        """
        Validate all query parameters in self.request against valid_params and
        add a 422 error at 'query'->key if the parameter key is invalid.
        Add validated parameters with values to self.request.validated_params.
        Ignore and drop validated parameters without values (e.g., "?q=&a=").
        """
        if not getattr(self.request, 'validated_params', None):
            self.request.validated_params = dict()

        for key in self.request.params:
            if key not in valid_params:
                self.request.errors.add(
                    'query', key,
                    "Unsupported query: {param}. Valid parameters: "
                    "{all}.".format(param=key, all=valid_params),
                )
                self.request.errors.status = 422
            elif self.request.params[key]:
                self.request.validated_params[key] = self.request.params[key]

    def validate_individual(self, request):
        """
        Validate that the resource with the given identifiers exists and
        attach it to the request at request.validated[name].
        This validator can raise a "400 Bad Request" error.
        """
        validator = getattr(
            self,
            'validate_individual_{name}'.format(
                name=self.name.replace('-', '_')
            ),
            None,
        )
        if validator:
            validator(request)
        else:
            self.get_obj_by_name_or_id()

    def validate_collection_get(self, request):
        """
        Make sure that the selection parameters are valid for resource type.
        If they are not, raise "400 Bad Request".
        Else, set request.validated[name] to resource matching query.
        """
        getter = getattr(
            self,
            'validate_{name}_collection'.format(
                name=self.name.replace('-', '_'),
            ),
            None
        )
        if getter is not None:
            getter(request)
        else:
            self.get_collection_by_limit_start()

    def _add_post_defaults(self):
        """
        Add the default values for fields if they are not passed in as params.
        """
        for attr in self.defaults:
            if attr not in self.request.validated_params:
                if type(self.defaults[attr]) == str:
                    self.request.validated_params[attr] = self.defaults[attr]
                else:
                    self.request.validated_params[attr] = self.defaults[attr](
                        self
                    )
        if not getattr(self, 'name', None):
            return
        if 'application' in self.request.validated:
            if 'package' in self.name:
                if 'job' not in self.request.validated_params:
                    self.request.validated_params['job'] = self.request.validated[
                        'application'
                    ].path

    def validate_put_post(self, _request):
        """
        Validate a PUT or POST request by validating all given attributes
        against the list of valid attributes for this view's associated model.
        """
        if getattr(self, '_handle_extra_params', None) is not None:
            self._handle_extra_params()
        self._validate_params(self.valid_attrs)
        self._validate_json_params()

    def validate_post_required(self, request):
        """
        Validate that the fields required for a POST are present in the
        parameters of the request.
        """
        for field in self.required_post_fields:
            if field not in request.validated_params:
                request.errors.add(
                    'query', '',
                    "{field} is a required field.".format(field=field)
                )
                request.errors.status = 400

    def validate_obj_put(self, _request):
        """
        Validate a PUT request by preventing collisions over unique fields.
        """
        func_name = 'validate_{name}_put'.format(
            name=self.name.replace('-', '_')
        )
        if getattr(self, func_name, None):
            getattr(self, func_name)()
        else:
            try:
                self._validate_name("PUT")
                self._validate_unique_together("PUT")
                self._validate_all_unique_params("PUT")
            except:
                raise NotImplementedError(
                    'A collision validator for this view has not been '
                    'implemented.'
                )

    def validate_obj_post(self, _request):
        """
        Validate a POST request by preventing collisions over unique fields.
        """
        self._add_post_defaults()
        if not getattr(self, 'name', None):
            return
        func_name = 'validate_{name}_post'.format(
            name=self.name.replace('-', '_')
        )
        if getattr(self, func_name, None):
            getattr(self, func_name)()
        else:
            try:
                self._validate_name("POST")
                self._validate_unique_together("POST")
                self._validate_all_unique_params("POST")
            except:
                raise NotImplementedError(
                    'A collision validator for this view has not been '
                    'implemented.'
                )

    def _validate_unique_together(self, request_type, obj_type=None):
        """
        Validate that any unique together constraints aren't violated.
        """
        if getattr(self, 'unique_together', None) is None:
            return
        if request_type == "PUT" and self.name not in self.request.validated:
            return
        if not obj_type:
            obj_type = self.name
        for tup in self.unique_together:
            tup_dict = dict()
            for item in tup:
                key = self.param_routes[item] if item in self.param_routes \
                    else item
                if request_type == "POST" and item not in \
                        self.request.validated_params:
                    continue
                tup_dict[key] = self.request.validated_params[item] if item \
                    in self.request.validated_params else \
                    getattr(self.request.validated[self.name], key)
            found = self.model.get(**tup_dict)
            if found is not None:
                if request_type == "POST":
                    self.request.errors.add(
                        'query', tup[-1],
                        "{tup} are unique together. A{mult} {obj_type} with "
                        "these attributes already exists.".format(
                            tup=tup,
                            mult='n' if obj_type[0] in 'aeiou' else '',
                            obj_type=obj_type,
                        )
                    )
                    self.request.errors.status = 409
                elif request_type == "PUT" and found != self.request.validated[
                    self.name
                ]:
                    self.request.errors.add(
                        'query', tup[-1],
                        "{tup} are unique together. Another {obj_type} with "
                        "these attributes already exists.".format(
                            tup=tup,
                            obj_type=obj_type,
                        )
                    )
                    self.request.errors.status = 409

    def _validate_all_unique_params(self, request_type):
        if getattr(self, 'unique', None) is None:
            return
        for param in self.unique:
            self._validate_unique_param(request_type, param)

    def _validate_name(self, request_type, obj_type=None):
        """
        Validate that the name unique constraint isn't violated for a request
        with either POST or PUT request_type.
        """
        self._validate_unique_param(request_type, "name", obj_type)

    def _validate_unique_param(self, request_type, param_name, obj_type=None,
                               msg_param_name=None):
        if not obj_type:
            obj_type = self.name
        if not msg_param_name:
            msg_param_name = param_name
        if param_name in self.request.validated_params:
            dict_key = self.param_routes[param_name] if param_name in \
                self.param_routes else param_name
            found_obj = self.model.get(
                **{dict_key: self.request.validated_params[param_name]}
            )
            if not found_obj:
                return
            elif request_type == 'POST':
                self.request.errors.add(
                    'query', param_name,
                    "Unique constraint violated. A{n} {type} with this {param}"
                    " already exists.".format(
                        n='n' if obj_type[0] in 'aeiou' else '',
                        type=obj_type,
                        param=msg_param_name,
                    )
                )
            elif obj_type not in self.request.validated:
                return
            elif found_obj != self.request.validated[obj_type]:
                self.request.errors.add(
                    'query', param_name,
                    "Unique constraint violated. Another {type} with this "
                    "{param} already exists.".format(
                        type=obj_type,
                        param=msg_param_name,
                    )
                )
            self.request.errors.status = 409

    def validate_obj_delete(self, request):
        """
        Validate that the object can be deleted.
        """
        if not getattr(self, 'name', None):
            return self.method_not_allowed(request)
        func_name = 'validate_{name}_delete'.format(
            name=self.name.replace('-', '_')
        )
        if getattr(self, func_name, None):
            self._validate_params(['cascade'])
            self._validate_json_params({'cascade': 'boolean'})
            self.request.validated['cascade'] = 'cascade' in \
                self.request.validated_params and \
                self.request.validated_params['cascade']
            getattr(self, func_name)()
        else:
            return self.method_not_allowed(request)

    def validate_cookie(self, request):
        """
        Validate the cookie in the request. If the cookie is valid, add a user
        to the request's validated_params dictionary.
        If the user is not authorized to do the current action, add the
        corresponding error.
        """
        (present, username, is_admin) = utils.validate_cookie(request,
                                                              self.settings)
        if not present:
            request.errors.add(
                'header', 'cookie',
                'Authentication required. Please login.'
            )
            if request.errors.status == 400:
                request.errors.status = 401
        elif not username:
            request.errors.add(
                'header', 'cookie',
                'Cookie has expired or is invalid. Please reauthenticate.'
            )
            if request.errors.status == 400:
                request.errors.status = 419
        else:
            request.validated['user'] = username
            request.is_admin = is_admin
            try:
                collection_path = self._services[
                    'collection_{name}'.format(
                        name=self.__class__.__name__.lower()
                    )
                ].path
            except KeyError:
                collection_path = None
            prefix = "collection_" if request.path == collection_path else ''
            if not getattr(self, 'permissions', None):
                return
            permissions_key = prefix + request.method.lower()
            if permissions_key not in self.permissions:
                return
            if self.permissions[permissions_key] == 'admin':
                if not request.is_admin:
                    request.errors.add(
                        'header', 'cookie',
                        'Admin authorization required. Please contact someone '
                        'in SiteOps to perform this operation for you.'
                    )
                    request.errors.status = 403

    def _validate_foreign_key(self, param_name, model_name, model,
                              attr_name=None):
        """
        Validate that a foreign key object with the name or ID in
        self.request.validated_params.
        If param_name is not in validated_params, just return.
        If an object with the name or ID can't be found, add an error to
        self.request.errors and set the status to 400.
        If attr_name is give, look for the name at that field in the model;
        otherwise, look in model.name
        """
        if param_name not in self.request.validated_params:
            return
        found = self._validate_foreign_key_existence(
            param_name,
            self.request.validated_params[param_name],
            model,
            model_name,
            attr_name
        )
        if found:
            self.request.validated_params[param_name] = found.id

    def _validate_foreign_key_existence(self, param_name, param, model,
                                        model_name, attr_name=None):
        """
        Verify that an object of type model with the given model_name exists
        and return it if it does.
        If it doesn't, set an error and return False
        """
        try:
            obj_id = int(param)
            found = model.get(id=obj_id)
            if found is None:
                self.request.errors.add(
                    'query', param_name,
                    "No {type} with ID {obj_id} exists.".format(
                        type=model_name,
                        obj_id=obj_id,
                    )
                )
                self.request.errors.status = 400
                return False
            return found
        except ValueError:
            name = param
            attrs = {attr_name: name} if attr_name else {'name': name}
            found = model.get(**attrs)
            if found is None:
                self.request.errors.add(
                    'query', param_name,
                    "No {type} with name {name} exists.".format(
                        type=model_name,
                        name=name
                    )
                )
                self.request.errors.status = 400
                return False
            return found

    def _validate_foreign_key_list(self, param_name, model_name, model,
                                   attr_name=None):
        """
        Validate the list or individual foreign key.
        """
        if param_name not in self.request.validated_params:
            return
        identifiers = self.request.validated_params[param_name].split(',')
        found_list = list()
        for identifier in identifiers:
            found = self._validate_foreign_key_existence(
                param_name,
                identifier,
                model,
                model_name,
                attr_name
            )
            if found:
                found_list.append(found)
        self.request.validated_params[param_name] = found_list

    def method_not_allowed(self, request):
        """
        Validator used to make methods not valid for a URL.
        """
        request.errors.add('url', 'method', "Method not allowed.")
        request.errors.status = 405
