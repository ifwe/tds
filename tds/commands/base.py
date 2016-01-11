"""
Base class for controllers.
"""

import tagopsdb.exceptions
import tds.model
import tds.authorize
import tds.exceptions


# TODO: these two functions should be methods on tds.model.*Target classes
def latest_deployed_package_for_app_target(environment, app, app_target):
    if isinstance(app, tds.model.Application):
        app = app.delegate

    for app_dep in app_target.app_deployments:
        if app_dep.environment != environment.environment:
            continue
        if app_dep.status == 'invalidated':
            continue
        if app_dep.package.application != app:
            continue

        return app_dep.package

    raise Exception(
        "no deployed version found for target \"%s\"",
        app_target.name
    )


def latest_deployed_version_for_host_target(environment, app, host_target):
    if isinstance(app, tds.model.Application):
        app = app.delegate

    for host_dep in reversed(host_target.host_deployments):
        if host_dep.package.application == app:
            return host_dep.package

    try:
        return latest_deployed_package_for_app_target(
            environment, app, host_target.application
        )
    except Exception:
        raise Exception(
            "no deployed version found for host \"%s\"",
            host_target.name
        )


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
                raise tds.exceptions.InvalidInputError(
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
                raise tds.exceptions.TDSException(
                    "Can't validate %r for class = %r",
                    key, type(self)
                )

            result.update(validator(**params))

        return result

    def validate_project(self, project=None, projects=None, **_params):
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
        missing_projects = []

        for project_name in projects:
            project = tds.model.Project.get(name=project_name)

            if project is None:
                missing_projects.append(project_name)
            else:
                project_objects.append(project)

        if len(missing_projects):
            raise tds.exceptions.NotFoundError('Project', missing_projects)

        return dict(
            projects=project_objects,
            project=project,
        )

    def validate_application(self, application=None, applications=None,
                             **_params):
        if applications is None:
            applications = []

        if application is not None:
            applications.append(application)

        application = None
        application_objects = []
        missing_applications = []

        for app in applications:
            if not isinstance(app, tds.model.Application):
                app_name = app
            else:
                app_name = app.name

            try:
                application = tds.model.Application.get(name=app_name)
            except tagopsdb.exceptions.MultipleInstancesException:
                raise tds.exceptions.MultipleResultsError(
                    'Multiple definitions for application found, '
                    'please file ticket in JIRA for TDS'
                )

            if application is None:
                missing_applications.append(app)
            else:
                application_objects.append(application)

        if len(missing_applications):
            raise tds.exceptions.NotFoundError('Application',
                                               missing_applications)

        return dict(
            application=application,
            applications=application_objects
        )

    def validate_targets(self, env, hosts=None, apptype=None, apptypes=None,
                         all_apptypes=None, **params):
        """
        Converts 'env', 'hosts', 'apptypes', and 'all_apptypes' parameters
        into just 'hosts' and 'apptypes' parameters.

        Verifies that all specified hosts/apptypes are in the right
        environments and associated with the project/projects.

        Can raise an Exception from various different failure modes.
        """

        if len(filter(None, [hosts, apptype, apptypes, all_apptypes])) > 1:
            raise tds.exceptions.ExclusiveOptionError(
                'These options are exclusive: %s',
                ', '.join(['hosts', 'apptypes', 'all-apptypes']))

        if apptype is not None:
            apptypes = [apptype]

        params.update(self.validate_application(**params))
        applications = params['applications']

        environment = tds.model.Environment.get(env=env)

        app_targets = []
        host_targets = []
        if not (hosts or apptypes):
            app_targets.extend(sum((app.targets for app in applications), []))
            if not all_apptypes and len(app_targets) > 1:
                raise tds.exceptions.TDSException(
                    "Specify a target constraint (too many targets found:"
                    " %s)", ', '.join(sorted([x.name for x in app_targets]))
                )
            return dict(apptypes=app_targets, hosts=None)
        elif apptypes:
            for app in applications:
                discovered_apptypes = set()
                for app_target in app.targets:
                    if app_target.name in apptypes:
                        app_targets.append(app_target)
                        discovered_apptypes.add(app_target.name)

                if discovered_apptypes != set(apptypes):
                    # "Apptypes dont all match. found=%r, wanted=%r",
                    # sorted(discovered_apptypes), sorted(set(apptypes))
                    raise tds.exceptions.InvalidInputError(
                        'Valid apptypes for application "%s" are: %r',
                        app.name, sorted(str(x.name) for x in app.targets)
                    )
            return dict(apptypes=app_targets, hosts=None)
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
                    host_targets.append(host)

            if no_exist_hosts:
                raise tds.exceptions.NotFoundError("Host",
                                                   sorted(no_exist_hosts))

            if bad_hosts:
                raise tds.exceptions.WrongEnvironmentError(
                    'These hosts are not in the "%s" environment: %s',
                    environment.environment, ', '.join(sorted(bad_hosts))
                )

            for app in applications:
                for host_target in host_targets:
                    if app not in host_target.target.package_definitions:
                        raise tds.exceptions.InvalidInputError(
                            'Application %s does not belong on host %s',
                            app.name, host_target.name
                        )

            return dict(hosts=host_targets, apptypes=None)

        raise NotImplementedError

    def validate_package(self, version=None, hostonly=False, show_cmd=False,
                         **params):
        params.update(self.validate_application(**params))
        application = params.pop('application')

        if version is None:
            package = self.get_latest_app_version(
                application, hostonly, show_cmd, **params
            )
            if package is None:
                raise Exception("Couldn't determine latest version")
        elif application is not None and len(application.packages) > 0:
            for package in application.packages:
                if version == package.version:
                    break
            else:
                package = None
        else:
            package = None

        if package is None:
            raise tds.exceptions.NotFoundError(
                'Package', ['{name}@{vers}'.format(name=application.name,
                                                   vers=version)]
            )

        return dict(package=package)

    def validate_package_hostonly(self, version=None, hostonly=True,
                                  **params):
        return self.validate_package(version, hostonly, **params)

    def validate_package_show(self, version=None, hostonly=False,
                              show_cmd=True, **params):
        return self.validate_package(version, hostonly, show_cmd, **params)

    def get_latest_app_version(self, app, hostonly, show_cmd, env, **params):
        # TODO: possibly move this to tds.model.Application ?
        targets = self.validate_targets(
            env=env,
            **params
        )

        host_targets = targets.get('hosts', None)
        app_targets = targets.get('apptypes', None)
        environment = tds.model.Environment.get(env=env)

        host_deployments = {}
        app_deployments = {}
        if hostonly:
            if host_targets is None:
                all_host_targets = []

                for app_target in app.targets:
                    all_host_targets.extend(app_target.hosts)

                host_targets = [
                    host_target for host_target in all_host_targets
                    if host_target.host_deployments
                    and host_target.environment == environment.environment
                ]

            for host_target in host_targets:
                host_deployments[host_target.id] = \
                    latest_deployed_version_for_host_target(
                        environment, app, host_target
                    )
        else:
            if app_targets is None:
                all_targets = app.targets
                app_target_ids = set()

                for host_target in host_targets:
                    common_targets = (
                        set([host_target.target.id]) &
                        set([x.id for x in all_targets])
                    )

                    if not common_targets:
                        raise tds.exceptions.InvalidOperationError(
                            'Host "%s" is not associated with '
                            'application "%s"',
                            host_target.name, app.name
                        )

                    app_target_ids = app_target_ids.union(common_targets)

                app_targets = [tds.model.AppTarget.get(id=id)
                               for id in app_target_ids]

            for app_target in app_targets:
                app_deployments[app_target.id] = \
                    latest_deployed_package_for_app_target(
                        environment, app, app_target
                    )

        if not (host_deployments or app_deployments):
            raise Exception(
                'Application "%s" has no current tier/host '
                'deployments to verify for the given apptypes/'
                'hosts', app.name
            )

        versions = dict(
            ((x.version, x.revision), x)
            for x in (host_deployments.values() + app_deployments.values())
        )

        if len(versions) > 1 and not show_cmd:
            raise ValueError(
                'Multiple versions not allowed, found: %r',
                list(sorted(versions.items()))
            )

        return versions.values()[0]
