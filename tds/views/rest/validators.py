"""
A view with validations or parameters given in request queries.
This class is separated out for separation of function.
Its only intended use is as a base class for the BaseView; directly importing
and using this view is discouraged.
"""

import tds.exceptions


class ValidatedView(object):
    """
    This class implements validators for parameters given in requests.
    """

    def _validate_params(self, valid_params):
        """
        Validate all query parameters in self.request against valid_param and
        add a 400 error at 'query'->key if the parameter key is invalid.
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
            elif self.request.params[key]:
                self.request.validated_params[key] = self.request.params[key]

    def _validate_model_params(self):
        """
        Validate all params in self.request.validated_params against each
        validator for that parameter given in the child class's
        types dict (self.types[param_name]).
        """
        self.validation_failures = dict()

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

            failure = validator(param)
            if failure:
                self.request.errors.add(
                    'query', param, "Validation failed: {msg}".format(
                        msg=failure
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
        if isinstance(given, bool):
            return False
        return ("Value {val} for argument {param} is not a Boolean,"
            " is {t}.".format(
                val=given, param=param_name, t=type(given)
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
