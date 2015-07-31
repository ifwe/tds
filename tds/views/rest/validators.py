"""
A view with validations or parameters given in request queries.
This class is separated out for separation of function.
Its only intended use is as a base class for the BaseView; directly importing
and using this view is discouraged.
"""

import datetime

import tds, tagopsdb

from . import utils


class JSONValidatedView(object):
    """
    This class implements JSON validators for parameters given in requests.
    """

    def _validate_model_params(self):
        """
        Validate all params in self.request.validated_params against each
        validator for that parameter given in the child class's
        types dict (self.types[param_name]).
        """
        for param in self.request.validated_params:
            if not param in self.types:
                continue
            validator_name = '_validate_' + self.types[param]
            validator = getattr(self, validator_name, None)
            if not validator:
                raise tds.exceptions.ProgrammingError(
                    "No validator found for type: {t}.".format(
                        t=validator_name
                    )
                )

            message = validator(param)
            if message:
                self.request.errors.add(
                    'query', param, "Validation failed: {msg}".format(
                        msg=message
                    )
                )

    def _validate_number(self, param_name):
        """
        Validate that the given param_name argument value in the query is a
        number and return False if it is; return an error message if it isn't.
        """
        given = self.request.validated_params[param_name]
        try:
            float(given)
        except ValueError:
            return (
                "Value {val} for argument {param} is not a number.".format(
                    val=given, param=param_name
                )
            )
        else:
            return False

    def _validate_integer(self, param_name):
        """
        Validate that the given param name argument value in the query is an
        integer and return False if it is; return an error message if it isn't.
        """
        given = self.request.validated_params[param_name]
        try:
            int(given)
        except ValueError:
            return (
                "Value {val} for argument {param} is not an integer.".format(
                    val=given, param=param_name
                )
            )
        else:
            return False

    def _validate_string(self, param_name):
        """
        Validate that the given param_name argument value in the query is a
        string and return False if it is; return an error message if it isn't.
        """
        given = self.request.validated_params[param_name]
        if isinstance(given, str) or isinstance(given, unicode):
            return False
        return (
            "Value {val} for argument {param} is not a string.".format(
                val=given, param=param_name
            )
        )

    def _validate_boolean(self, param_name):
        """
        Validate that the given param_name argument value in the query is a
        string and return False if it is; return an error message if it isn't.
        """
        given = self.request.validated_params[param_name]
        if given in ('0', '1', 'true', 'false', 'True', 'False'):
            self.request.validated_params[param_name] = given in ('1', 'true',
                                                                  'True')
            return False
        return (
            "Value {val} for argument {param} is not a Boolean. Valid Boolean"
            " formats: (0, 1, 'true', 'false', 'True', 'False').".format(
                val=given, param=param_name
            )
        )

    def _validate_timestamp(self, param_name):
        """
        Validate that the given param_name argument value in the query is a
        date following the specification in
        /doc/rest_api.md#Attributes.Timestamps, set the value to the parsed
        date and return False if it is; return an error message if it isn't.
        """
        given = self.request.validated_params[param_name]
        try:
            date_format = "%Y-%m-%dT%H:%M:%S"
            date = datetime.datetime.strptime(given[:19], date_format)
            rem = float(given[19:26]) + int(given[26:29]) * 3600 \
                + int(given[29:31]) * 60
            date += datetime.timedelta(seconds=rem)
        except:     #TODO: Figure out which exceptions will be thrown here.
            return "Could not parse {val} for {param} as a valid timestamp."\
                .format(val=given, param=param_name)
        else:
            self.request.validated_params[param_name] = date
            return False

    def _validate_choice(self, param_name):
        """
        Validate that the given param_name argument value in the query is in
        self.<param_name>_choices and return False if it is; return an error
        message if it isn't.
        """
        given = self.request.validated_params[param_name]
        choices = getattr(self, "{param}_choices".format(param=param_name))
        if given not in choices:
            return (
                "Value {val} for argument {param} must be one of: "
                "{choices}.".format(
                    val=given, param=param_name, choices=choices
                )
            )
        else:
            return False


class ValidatedView(JSONValidatedView):
    """
    This class implements common non-JSON validators.
    """

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
            obj_dict = dict()
            if 'name' in self.param_routes:
                obj_dict[self.param_routes['name']] = name
            else:
                obj_dict['name'] = name
            obj = obj_cls.get(**obj_dict)

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
        else:
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
        if self.name == 'package':
            self.get_obj_by_name_or_id('application')
            if 'application' in request.validated:
                self.get_pkg_by_version_revision()
        else:
            self.get_obj_by_name_or_id()

    def validate_collection_get(self, request):
        """
        Make sure that the selection parameters are valid for resource type.
        If they are not, raise "400 Bad Request".
        Else, set request.validated[name] to resource matching query.
        """
        if self.name == 'package':
            self.get_obj_by_name_or_id('application')
            if 'application' in request.validated:
                self.get_pkgs_by_limit_start()
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
        if self.name == 'package' and 'application' in self.request.validated:
            if 'job' not in self.request.validated_params:
                self.request.validated_params['job'] = self.request.validated[
                    'application'
                ].path

    def validate_put_post(self, _request):
        """
        Validate a PUT or POST request by validating all given attributes
        against the list of valid attributes for this view's associated model.
        """
        self._validate_params(self.valid_attrs)
        self._validate_model_params()
        self._add_post_defaults()

    def validate_post_required(self, _request):
        """
        Validate that the fields required for a POST are present in the
        parameters of the request.
        """
        for field in self.required_post_fields:
            if field not in self.request.validated_params:
                self.request.errors.add(
                    'query', '',
                    "{field} is a required field.".format(field=field)
                )
                self.request.errors.status = 400

    def validate_obj_put(self, _request):
        """
        Validate a PUT request by preventing collisions over unique fields.
        """
        if self.name in ('application', 'project'):
            self.validate_app_proj_put()
        elif self.name == 'package':
            self.validate_pkg_put()
        elif self.name == 'tier':
            self.validate_tier_put()
        elif self.name == 'host':
            self.validate_host_put()
        elif self.name == 'ganglia':
            self.validate_ganglia_put()
        else:
            raise NotImplementedError(
                'A collision validator for this view has not been implemented.'
            )

    def _validate_id(self, request_type):
        """
        Validate that the ID unique constraint isn't violated for a request
        with either POST or PUT request_type.
        """
        if 'id' in self.request.validated_params:
            found_obj = self.model.get(id=self.request.validated_params['id'])
            if not found_obj:
                return
            elif request_type == 'POST':
                self.request.errors.add(
                    'query', 'id',
                    "Unique constraint violated. A{n} {type} with this ID"
                    " already exists.".format(
                        n='n' if self.name[0] in 'aeiou' else '',
                        type=self.name
                    )
                )
            elif found_obj != self.request.validated[self.name]:
                self.request.errors.add(
                    'query', 'id',
                    "Unique constraint violated. Another {type} with this"
                    " ID already exists.".format(type=self.name),
                )
            self.request.errors.status = 409

    def _validate_name(self, request_type):
        """
        Validate that the name unique constraint isn't violated for a request
        with either POST or PUT request_type.
        """
        if 'name' in self.request.validated_params:
            dict_key = 'name'
            if 'name' in self.param_routes:
                dict_key = self.param_routes['name']
            found_obj = self.model.get(
                **{dict_key: self.request.validated_params['name']}
            )
            if not found_obj:
                return
            elif request_type == 'POST':
                self.request.errors.add(
                    'query', 'name',
                    "Unique constraint violated. A{n} {type} with this name"
                    " already exists.".format(
                        n='n' if self.name[0] in 'aeiou' else '',
                        type=self.name,
                    )
                )
            elif found_obj != self.request.validated[self.name]:
                self.request.errors.add(
                    'query', 'name',
                    "Unique constraint violated. Another {type} with this"
                    " name already exists.".format(type=self.name)
                )
            self.request.errors.status = 409

    def validate_app_proj_put(self):
        """
        Validate a PUT request by preventing collisions over unique fields for
        applications and projects.
        """
        self._validate_id("PUT")
        self._validate_name("PUT")

    def validate_cookie(self, _request):
        """
        Validate the cookie in the request. If the cookie is valid, add a user
        to the request's validated_params dictionary.
        """
        (present, username) = utils.validate_cookie(self.request,
                                                    self.settings)
        if not present:
            self.request.errors.add(
                'header', 'cookie',
                'Authentication required. Please login.'
            )
            if self.request.errors.status == 400:
                self.request.errors.status = 401
        elif not username:
            self.request.errors.add(
                'header', 'cookie',
                'Cookie has expired or is invalid. Please reauthenticate.'
            )
            if self.request.errors.status == 400:
                self.request.errors.status = 419
        else:
            self.request.validated['user'] = username

    def _validate_foreign_key(self, param_name, model_name, model,
                              attr_name=None):
        """
        Validate that a foreign key object with the name or ID in
        self.request.validated_params.
        If param_name is not in validated_params, just return.
        If an object with the name or ID can't be found, add an error to
        self.request.errors and set the status to 400.
        If name_param is give, look for the name at that field in the model;
        otherwise, look in model.name
        """
        if param_name not in self.request.validated_params:
            return
        try:
            obj_id = int(self.request.validated_params[param_name])
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
        except ValueError:
            if self.request.errors.status == 400:
                return
            name = self.request.validated_params[param_name]
            attrs = dict()
            if attr_name:
                attrs[attr_name] = name
            else:
                attrs['name'] = name
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
