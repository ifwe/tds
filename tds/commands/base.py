import collections

import tds.model
import tds.authorize
import tds.exceptions

def validate(attr):
    def function(f):
        needs_val = getattr(f, '_needs_validation', None)
        if needs_val is None:
            needs_val = f._needs_validation = []
        needs_val.append(attr)

        return f
    return function

class BaseController(object):
    access_levels = {}

    def __init__(self, config):
        self.app_config = config

    def action(self, action, **params):
        required_access_level = self.access_levels.get(action, 'disabled')

        if required_access_level is not None:
            if required_access_level == 'environment':
                required_access_level = params.get('environment')

            try:
                tds.authorize.verify_access(
                    params.get('user_level', 'disabled'),
                    required_access_level
                )
            except tds.exceptions.AccessError as exc:
                return dict(error=exc)


        handler = getattr(self, action, None)
        params = self.validate_params(
            getattr(handler, '_needs_validation', None),
            params
        )

        if handler is None:
            return dict(error=Exception(
                "Unknown action for %s: %s", type(self).__name__, action
            ))

        try:
            return handler(**params)
        except Exception as exc:
            return dict(error=exc)

    def validate_params(self, validate_attrs, params):
        if not validate_attrs:
            return params

        result = params.copy()

        for key in params.keys():
            if key not in validate_attrs:
                continue

            validator = getattr(self, 'validate_' + key, None)
            if validator is None:
                raise Exception(
                    "Can't validate %r for class = %r",
                    key, type(self)
                )

            result.update(validator(**params))

        return result


    def validate_project(self, project=None, projects=None, **params):
        if projects is None:
            projects = []

        if project is not None:
            projects.append(project)

        project = None
        project_objects = []

        for project_name in projects:
            project = tds.model.Project.get(name=project_name)
            if project is None:
                raise Exception('Project "%s" does not exist', project_name)

            project_objects.append(project)

        return dict(
            projects=project_objects,
            project=project,
        )
