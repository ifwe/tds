"""
Base class for controllers.
"""

import argparse

import tds.model
import tds.authorize
import tds.exceptions


def latest_deployed_package_for_app_target(environment, app, app_target):
    for app_dep in reversed(app_target.app_deployments):
        if app_dep.environment != environment.environment:
            print "environment didn't match", environment, app_dep
            continue
        if app_dep.status == 'invalidated':
            print "bad status", app_dep.status
            continue
        if app_dep.deployment.package.application != app:
            print "wrong app somehow", app_dep.deployment.package.application, app
            continue

        return app_dep.deployment.package

    raise Exception(
        "no deployed version found for target \"%s\"",
        app_target.name
    )

def latest_deployed_version_for_host_target(environment, app, host_target):
    for host_dep in reversed(host_target.host_deployments):
        if host_dep.deployment.package.application == app:
            return host_dep.deployment.package

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

            if len(project.applications) == 0:
                raise Exception(
                    'Project "%s" has no applications', project_name,
                )

            if len(project.applications) > 1:
                raise Exception(
                    'Project "%s" has too many applications: %s',
                    project_name,
                    sorted(', '.join(x.name for x in project.applications))
                )

            project_objects.append(project)

        return dict(
            projects=project_objects,
            project=project,
        )

    def validate_application(self, application=None, applications=None, **params):
        if applications is None:
            applications = []

        if application is not None:
            applications.append(application)

        application = None
        application_objects = []

        for app in applications:
            application = tds.model.Application.get(name=app)

            if application is None:
                raise Exception("Couldnt find app: %r", app)

            application_objects.append(application)

        return dict(
            application=application,
            applications=application_objects
        )


    def validate_targets(
        self, env, hosts=None, apptype=None, apptypes=None, all_apptypes=None, **params
    ):
        """
        Converts 'env', 'hosts', 'apptypes', and 'all_apptypes' parameters
        into just 'hosts' and 'apptypes' parameters.

        Verifies that all specified hosts/apptypes are in the right
        environments and associated with the project/projects.

        Can raise an Exception from various different failure modes.
        """

        if len(filter(None, [hosts, apptype, apptypes, all_apptypes])) > 1:
            raise argparse.ArgumentError('These options are exclusive: %s'
                ['hosts', 'apptypes', 'all_apptyes']
            )

        if apptype is not None:
            apptypes = [apptype]

        params.update(self.validate_project(**params))
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

    def validate_package(self, version=None, **params):
        params.update(self.validate_application(**params))
        project = params.pop('project', None)
        application = params.pop('application')
        applications = params.pop('applications', [])

        if len(applications) > 1:
            raise Exception(
                'Project "%s" has too many applications associated with it: %s',
                getattr(project, 'name', None),
                sorted(x.name for x in applications)
            )

        if version is None:
            package = self.get_latest_app_version(None, application, **params)
            if package is None:
                raise Exception("couldnt determine latest version")
        else:
            for package in application.packages:
                if version == package.version:
                    break
            else:
                package = None

        if package is None:
            raise Exception(
                'Package "%s@%s" does not exist',
                application.name, version
            )

        return dict(package=package)

    def get_latest_app_version(self, project, app, env, **params):
        targets = self.validate_targets(project=project.name, env=env, **params)

        host_targets = targets.get('hosts', None)
        app_targets = targets.get('apptypes', None)
        environment = tds.model.Environment.get(env=env)

        host_deployments = {}
        app_deployments = {}
        if host_targets:
            for host_target in host_targets:
                host_deployments[host_target.id] = \
                    latest_deployed_version_for_host_target(
                        environment, app, host_target
                    )
        else:
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

        if len(versions) > 1:
            raise ValueError(
                'Multiple versions not allowed, found: %r',
                list(sorted(versions.items()))
            )

        return versions.values()[0]
