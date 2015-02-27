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
        validators dict (self.validators[param_name]).
        """
        if not getattr(self.request, 'validated_params', None):
            raise tds.exceptions.IllegalStateError(
                "No validated parameters in request."
            )

        self.validation_failures = dict()

        for param in self.request.validated_params:
            if not param in self.validators:
                continue
            validator_name = self.validators[param]
            validator = getattr(self, validator_name, None)
            if not validator:
                raise tds.exceptions.ProgrammingError(
                    "No validator found: {v}.".format(v=validator_name)
                )

            failure = validator(param)
            if failure:
                self.request.errors.add(
                    'query', param, "Validation failed"
                )

        for index, tup in enumerate(getattr(self, 'unique_together', list())):
            failure = self._validate_unique_together(tup)
            if failure:
                self.request.errors.add(
                    'query', self.unique_together[index][0],
                    "Unique together constraint broken: "
                    "{all}.".format(
                        all=self.unique_together[index]
                    )
                )

    def _validate_unique(self, param_name):
        """
        Validate that it is okay to add an object with the given unique attr
        to the database for this view's model.
        If it is, return False. Return a descriptive message otherwise.
        """
        given = self.request.validated_params[param_name]
        found = self.model.find(
            getattr(self.model, param_name) == given
        )
        if not found:
            return False
        elif self.name in self.request.validated and \
                found.one() == self.request.validated[self.name]:
            return False
        return "Unique constraint broken: {param}.".format(param=param_name)

    def _validate_fqdn(self, param_name):
        """
        Validate that the param value for param_name is a legal fully
        qualified domain name.
        """
        pass
        #TODO: implement this.

    def _validate_unique_together(self, param_names):
        """
        Validate that it is okay to add an object with the given param values
        which should be unique together in the database.
        """
        query = self.model.query()
        for param_name in param_names:
            query.filter(
                getattr(self.model, param_name) == \
                self.request.validated_params[param_name]
            )
        found = query.one()
        if not found:
            return False
        elif self.name in self.request.validated and \
                found == self.request.validated[self.name]:
            return False
        return "Unique constraint broken: {params}.".format(
            params=param_names
        )
