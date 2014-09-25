"""
Base class for controllers.
"""

import argparse

import tds.model
import tds.authorize
import tds.exceptions


def validate(attr):
    """
    Decorator for an action method, which
    """
    def function(func):
        """
        Adds an attr to the func's _needs_validation list
        """
        needs_val = getattr(func, '_needs_validation', None)
        if needs_val is None:
            needs_val = func._needs_validation = []
        needs_val.append(attr)

        return func
    return function


class BaseController(object):
    """
    Base class for controllers.
    """
    access_levels = {}

    def __init__(self, config):
        self.app_config = config

    def action(self, action, **params):
        """
        Perform an action for the controller with authorization, input
        validation, and exception handling.
        """
        required_access_level = self.access_levels.get(action, 'disabled')

        if required_access_level is not None:
            if required_access_level == 'environment':
                required_access_level = params.get('env')

            try:
                tds.authorize.verify_access(
                    params.get('user_level', 'disabled'),
                    required_access_level
                )
            except tds.exceptions.AccessError as exc:
                return dict(error=exc)

        handler = getattr(self, action, None)

        try:
            if handler is None:
                raise Exception(
                    "Unknown action for %s: %s", type(self).__name__, action
                )

            # TODO: turn validation errors into a different kind of exception
            params = self.validate_params(
                getattr(handler, '_needs_validation', None),
                params
            )

            for key in params.keys():
                if params[key] is None:
                    params.pop(key)

            return handler(**params)
        except Exception as exc:

            return dict(error=exc)

    def validate_params(self, validate_attrs, params):
        """
        Validates various parameters. See `validate_*` functions for different
        parameters that can be validated and how.
        """
        if not validate_attrs:
            return params

        result = params.copy()

        for key in validate_attrs:
            validator = getattr(self, 'validate_' + key, None)
            if validator is None:
                raise Exception(
                    "Can't validate %r for class = %r",
                    key, type(self)
                )

            result.update(validator(**params))

        return result

    def validate_project(self, project=None, projects=None, **params):
        """
        Converts 'project' and 'projects' parameters from string names that
        identify the projects into Project instances.

        Can raise an Exception if a Project cannot be found for a name.
        """
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

    def validate_targets(
        self, env, hosts=None, apptypes=None, all_apptypes=None, **params
    ):
        """
        Converts 'env', 'hosts', 'apptypes', and 'all_apptypes' parameters
        into just 'hosts' and 'apptypes' parameters.

        Verifies that all specified hosts/apptypes are in the right
        environments and associated with the project/projects.

        Can raise an Exception from various different failure modes.
        """

        if len(filter(None, [hosts, apptypes, all_apptypes])) > 1:
            raise argparse.ArgumentError('These options are exclusive: %s'
                                         ['hosts', 'apptypes', 'all_apptyes'])

        params = self.validate_project(**params)
        projects = params['projects']

        environment = tds.model.Environment.get(env=env)

        targets = []
        if not (hosts or apptypes):
            targets.extend(sum((p.targets for p in projects), []))
            if not all_apptypes and len(targets) > 1:
                raise Exception(
                    "Specify a target constraint (too many targets found: %s)",
                    ', '.join(sorted([x.name for x in targets]))
                )
            return dict(apptypes=targets, hosts=None)
        elif apptypes:
            for proj in projects:
                discovered_apptypes = set()
                for targ in proj.targets:
                    if targ.name in apptypes:
                        targets.append(targ)
                        discovered_apptypes.add(targ.name)

                if discovered_apptypes != set(apptypes):
                    # "Apptypes dont all match. found=%r, wanted=%r",
                    # sorted(discovered_apptypes), sorted(set(apptypes))
                    raise Exception(
                        'Valid apptypes for project "%s" are: %r',
                        proj.name, sorted(str(x.name) for x in proj.targets)
                    )
            return dict(apptypes=targets, hosts=None)
        elif hosts:
            bad_hosts = []
            no_exist_hosts = []
            for hostname in hosts:
                host = tds.model.HostTarget.get(
                    name=hostname,
                )
                if host is None:
                    no_exist_hosts.append(hostname)
                    continue
                if host.environment != environment.environment:
                    bad_hosts.append(host.name)
                else:
                    targets.append(host)

            if no_exist_hosts:
                raise Exception(
                    "These hosts do not exist: %s",
                    ', '.join(sorted(no_exist_hosts))
                )

            if bad_hosts:
                raise Exception(
                    'These hosts are not in the "%s" environment: %s',
                    environment.environment, ', '.join(sorted(bad_hosts))
                )

            for project in projects:
                for target in targets:
                    if project not in target.application.projects:
                        raise Exception(
                            "Host %r not a part of project %r",
                            target, project
                        )

            return dict(hosts=targets, apptypes=None)

        raise NotImplementedError
