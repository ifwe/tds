"""
JSON validators class, to be used as a base class for the ValidatedView class.
"""


import datetime

import tds


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

    def _validate_integer_list(self, param_name):
        """
        Validate that the given param name argument value in the query is an
        integer list and return False if it is; return an error message if it
        isn't.
        """
        given = self.request.validated_params[param_name].split(',')
        for item in given:
            try:
                int(given)
            except ValueError:
                return (
                    "Value {val} for argument {param} is not a comma-separated"
                    " list of integers.".format(val=give, param=param_name)
                )

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
