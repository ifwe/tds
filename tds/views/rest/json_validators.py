# Copyright 2016 Ifwe Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
JSON validators class, to be used as a base class for the ValidatedView class.
"""


import os
import datetime
import yaml

from os.path import join as opj

import tagopsdb
import tds
import tds.utils.config


class JSONValidatedView(object):
    """
    This class implements JSON validators for parameters given in requests.
    """

    VALID_BOOLEAN_TRUE_VALUES = ('1', 'true', 'True')
    VALID_BOOLEAN_FALSE_VALUES = ('0', 'false', 'False')
    VALID_BOOLEAN_VALUES = tuple(
        list(VALID_BOOLEAN_TRUE_VALUES) +
        list(VALID_BOOLEAN_FALSE_VALUES)
    )

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

        settings_path = None
        local_path = opj(os.path.dirname(os.path.realpath(__file__)),
                         'settings.yml')
        global_path = opj(tds.utils.config.TDSConfig.default_conf_dir,
                          'deploy.yml')
        if os.path.exists(local_path):
            settings_path = local_path
        elif os.path.exists(global_path):
            settings_path = global_path
        else:
            raise tds.exceptions.ConfigurationError(
                "Could not find REST settings file at {local_path} "
                "or {global_path}.".format(local_path=local_path,
                                           global_path=global_path)
            )

        try:
            with open(settings_path) as settings_file:
                self.settings = yaml.load(settings_file.read())
                if settings_path == global_path:
                    tds_rest_path = opj(
                        tds.utils.config.TDSConfig.default_conf_dir,
                        'tds_rest.yml'
                    )
                    with open(tds_rest_path) as tds_rest_file:
                        data = yaml.load(tds_rest_file.read())
                        for key in data:
                            self.settings[key] = data[key]
                else:
                    # This is so the feature test suite will work
                    self.settings['url_prefix'] = ''
        except IOError:
            raise tds.exceptions.ConfigurationError(
                "Could not open REST settings file {path}."
                .format(path=settings_path)
            )
        if self.valid_attrs and len(self.types) > 0:
            for param in [x for x in self.types if self.types[x] == 'choice']:
                choices = getattr(
                    self, '{param}_choices'.format(param=param), None
                )
                if choices is None or len(choices) == 0:
                    try:
                        if getattr(self.model, 'delegate', None):
                            table = self.model.delegate.__table__
                        else:
                            table = self.model.__table__
                        col_name = self.param_routes.get(param, param)
                        setattr(
                            self,
                            '{param}_choices'.format(param=param),
                            table.columns[col_name].type.enums
                        )
                    except Exception as exc:
                        raise tds.exceptions.ProgrammingError(
                            "No choices set for param {param}. "
                            "Got exception {e}.".format(param=param, e=exc)
                        )

        self.session = tagopsdb.model.Base.Session()
        super(JSONValidatedView, self).__init__(*args, **kwargs)

    def _validate_json_params(self, types=None):
        """
        Validate all params in self.request.validated_params against each
        validator for that parameter given in the child class's
        types dict (self.types[param_name]) or with types if given.
        """
        if types is None:
            types = self.types
        for param in self.request.validated_params:
            if not param in types:
                continue
            validator_name = '_validate_' + types[param]
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
                self.request.errors.status = 400

    def _get_param_value(self, param_name, types=None):
        """
        Return the value of the param with name param_name from
        self.request.validated_params, cast as its type declared in types, if
        present in types. Otherwise, just return
        self.request.validated_params[param_name].
        param_name should be the name of the param and should be a key in
        self.request.validated_params.
        types should be a dict mapping param names to their types. If types is
        None, self.types is used instead.
        """
        if types is None:
            types = self.types
        if param_name not in types:
            return self.request.validated_params.get(param_name)
        param_type = types[param_name]
        raw_value = self.request.validated_params[param_name]
        if param_type == 'number':
            return float(raw_value)
        elif param_type == 'integer':
            return int(raw_value)
        elif param_type == 'boolean':
            return raw_value in self.VALID_BOOLEAN_TRUE_VALUES
        return raw_value

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
                int(item)
            except ValueError:
                return (
                    "Value {val} for argument {param} is not a comma-separated"
                    " list of integers.".format(val=item, param=param_name)
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
        if given in self.VALID_BOOLEAN_VALUES:
            self.request.validated_params[param_name] = given in \
                self.VALID_BOOLEAN_TRUE_VALUES
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
        time_fmt = "%Y-%m-%d %H:%M:%S"
        if getattr(self.request, 'validated', None) is None:
            self.request.validated = dict()
        try:
            int_given = int(given)
            self.request.validated[param_name] = \
                datetime.datetime.fromtimestamp(int_given).strftime(time_fmt)
            return False
        except ValueError:
            epoch = datetime.datetime.fromtimestamp(0)
            try:
                parsed = \
                    datetime.datetime.strptime(given[:19], "%Y-%m-%dT%H:%M:%S")
                self.request.validated[param_name] = parsed.strftime(time_fmt)
                return False
            except ValueError:
                try:
                    parsed = \
                        datetime.datetime.strptime(given[:10], "%Y-%m-%d")
                    self.request.validated[param_name] = parsed.strftime(
                        time_fmt
                    )
                    return False
                except ValueError:
                    return (
                        "Could not parse {val} for {param} as a valid "
                        "timestamp. Valid timestamp formats: %Y-%m-%d, "
                        "%Y-%m-%dT%H:%M:%S, and integer seconds since epoch."
                        .format(
                            val=given, param=param_name
                        )
                    )

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
                    val=given, param=param_name,
                    choices=sorted(str(choice) for choice in choices),
                )
            )
        else:
            return False
