"""
A view with validations or parameters given in request queries.
This class is separated out for separation of function.
Its only intended use is as a base class for the BaseView; directly importing
and using this view is discouraged.
"""

import tds.exceptions


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
            return ("Value {val} for argument {param} is not a number,"
                " is {t}.".format(
                    val=given, param=param_name, t=type(given)
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
        return ("Value {val} for argument {param} is not a string,"
            " is {t}.".format(
                val=given, param=param_name, t=type(given)
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
        print "given:", given
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
                    "{all}.".format(param=key, all=valid_params)
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
                self.request.validated_params[attr] = self.defaults[attr]

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
        else:
            raise NotImplementedError(
                'A collision validator for this view has not bee implemented.'
            )

    def _validate_put_id(self):
        """
        Validate that the ID unique constraint isn't violated by a PUT request.
        """
        if 'id' in self.request.validated_params:
            found_obj = self.model.get(id=self.request.validated_params['id'])
            if found_obj and found_obj != self.request.validated[self.name]:
                self.request.errors.add(
                    'query', 'id',
                    "Unique constraint violated. Another {type} with this"
                    " ID already exists.".format(type=self.name)
                )
                self.request.errors.status = 409

    def validate_app_proj_put(self):
        """
        Validate a PUT request by preventing collisions over unique fields for
        applications and projects.
        """
        self._validate_put_id()
        if 'name' in self.request.validated_params:
            found_obj = self.model.get(
                name=self.request.validated_params['name']
            )
            if found_obj and found_obj != self.request.validated[self.name]:
                self.request.errors.add(
                    'query', 'name',
                    "Unique constraint violated. Another {type} with this"
                    " name already exists.".format(type=self.name)
                )
                self.request.errors.status = 409
