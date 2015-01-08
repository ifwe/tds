"""
A command line view for TDS
"""

import json

from tabulate import tabulate

from .base import Base
from .json_encoder import TDSEncoder


def silence(*exc_classes):
    """
    Create a function to silence given exception classes when excecuting
    a function.
    """
    def wrap_func(func):
        """Wrapper for exception silencing function."""
        def call_func(*a, **k):
            """Exception silencing function."""
            try:
                return func(*a, **k)
            except exc_classes:
                return None
        return call_func
    return wrap_func

# Mapping of output_format argument to tabulate's tablefmt argument.
TABULATE_FORMAT = {
    'table': 'orgtbl',
    'rst': 'rst',
    'latex': 'latex',
}

# TODO: this isn't planned out AT ALL
PROJECT_TEMPLATE = (
    'Project: {self.name}\n'
    # 'Project type: {self.type}\n'
)
APP_TEMPLATE = (
    'Application name: {self.pkg_name}\n'
    'Architecture: {self.arch}\n'
    'Path: {self.path}\n'
    'Build host: {self.build_host}\n'
)
TARGET_TEMPLATE = ('App types: {s}\n')
APPLICATION_TEMPLATE = (
    'Application: {self.pkg_name}\n'
    'Deploy type: {self.deploy_type}\n'
    'Architecture: {self.arch}\n'
    'Build system type: {self.build_type}\n'
    'Build host: {self.build_host}\n'
    'Path: {self.path}\n'
)
PKG_DEPLOY_HEADER_TEMPLATE = (
    'Deployments of package {pkg_dep[pkg_def].name} '
    'to the following tiers:\n'
    '==========\n'
)
PKG_DEPLOY_MISSING_TEMPLATE = (
    'No deployments of package {pkg_dep[pkg_def].name} '
    'to any of the given tiers\n'
)
APP_DEPLOY_HEADER_TEMPLATE = (
    'Deployment of {app_dep.deployment.package.name} '
    'to {app_dep.application.name} tier '
    'in {app_dep.environment} environment:\n'
    '==========\n'
)
APP_DEPLOY_MISSING_TEMPLATE = (
    'No deployments to tiers for {app_dep[pkg_def].name} '
    '(for possible given version) yet '
    'in {app_dep[environment]} environment\n'
)
APP_DEPLOY_TEMPLATE = (
    'Version: {app_dep.deployment.package.version}-'
    '{app_dep.deployment.package.revision}\n'
    'Declared: {app_dep.deployment.declared}\n'
    'Declaring user: {app_dep.deployment.user}\n'
    'Realized: {app_dep.realized}\n'
    'Realizing user: {app_dep.user}\n'
    'App type: {app_dep.application.name}\n'
    'Environment: {app_dep.environment}\n'
    'Deploy state: {app_dep.deployment.dep_type}\n'
    'Install state: {app_dep.status}\n'
)
HOST_DEPLOY_HEADER_TEMPLATE = (
    'Deployment of {host_dep[pkg_def].name} to hosts '
    'in {host_dep[environment]} environment:\n'
    '==========\n'
)
# Note: the following template is unused for now and may be
#       removed in the near future
HOST_DEPLOY_MISSING_TEMPLATE = (
    'No deployments to hosts for {host_dep[pkg_def].name} '
    '(for possible given version) '
    'in {host_dep[environment]} environment\n'
)
HOST_DEPLOY_TEMPLATE = (
    'Version: {host_dep.deployment.package.version}-'
    '{host_dep.deployment.package.revision}\n'
    'Declared: {host_dep.deployment.declared}\n'
    'Declaring user: {host_dep.deployment.user}\n'
    'Realized: {host_dep.realized}\n'
    'Realizing user: {host_dep.user}\n'
    'Hostname: {host_dep.host.name}\n'
    'Deploy state: {host_dep.deployment.dep_type}\n'
    'Install state: {host_dep.status}\n'
)

PACKAGE_TEMPLATE = (
    'Project: {self.name}\n'
    'Version: {self.version}\n'
    'Revision: {self.revision}\n'
)


def format_access_error(_exc):
    """Format an access error."""
    return (
        'You do not have the appropriate permissions to run this command. '
        'Contact your manager.'
    )


EXCEPTION_FORMATTERS = dict(
    AccessError=format_access_error
)


def format_exception(exc):
    """Format an exception for user consumption."""

    exception_formatter = EXCEPTION_FORMATTERS.get(
        type(exc).__name__,
        format_exception_default
    )

    try:
        return exception_formatter(exc)
    except Exception as format_exc:
        return (
            "Exception=repr(%r) str(%s) could not be formatted: %r" %
            (exc, exc, format_exc)
        )


def format_exception_default(exc):
    """Default exception formatter."""
    return exc.args[0] % exc.args[1:]


def format_project(proj_result, output_format="blocks"):
    """
    Format a project object or iterable of projects in given output_format.
    """
    #TODO Output exceptions in some of these output formats.
    if output_format == "json":
        return json.dumps(proj_result, cls=TDSEncoder)
    try:
        iterable = iter(proj_result)
    except TypeError:
        iterable = False
    if not iterable and isinstance(proj_result, Exception):
        return format_exception(proj_result)
    if output_format == "blocks":
        if iterable:
            return reduce(lambda x, y: x + '\n\n' + y,
                          (format_project(p, "blocks")
                           if not isinstance(p, Exception)
                           else format_exception(p) for p in proj_result), "")
        else:
            output = []
            output.append(PROJECT_TEMPLATE.format(self=proj_result))
            for app in proj_result.applications:
                app_result = []
                app_info = APP_TEMPLATE.format(self=app)
                app_result.extend(app_info.splitlines())
                app_names = set(x.name for x in proj_result.applications)
                app_result.append(TARGET_TEMPLATE.format(
                    s=', '.join(
                        x.name.encode('utf8') for x in
                        sorted(
                            proj_result.targets,
                            key=lambda target: target.name.lower
                        )
                        if set(
                            p.name for p in x.package_definitions
                        ) & app_names
                    )
                ))
                output.append('\n\t'.join(app_result))

            return ''.join(output) + '\n'
    else:
        if iterable:
            return tabulate(tuple((p.name,) for p in proj_result
                                  if not isinstance(p, Exception)),
                            headers=("Project",),
                            tablefmt=TABULATE_FORMAT[output_format])
        else:
            return tabulate(((proj_result.name,),), headers=("Project",),
                            tablefmt=TABULATE_FORMAT[output_format])


def format_application(app_result, output_format="blocks"):
    """Format an application object or iterable of applications in
       given output format
    """
    if output_format == "json":
        return json.dumps(app_result, cls=TDSEncoder)
    try:
        iterable = iter(app_result)
    except TypeError:
        iterable = False
    if not iterable and isinstance(app_result, Exception):
        return format_exception(app_result)
    if output_format == "blocks":
        if iterable:
            return reduce(lambda x, y: x + '\n\n' + y,
                          (format_application(p, "blocks")
                           if not isinstance(p, Exception)
                           else format_exception(p) for p in app_result), "")
        else:
            return APPLICATION_TEMPLATE.format(self=app_result)
    else:
        if iterable:
            return tabulate(tuple((p.name,) for p in app_result
                                  if not isinstance(p, Exception)),
                            headers=("Application",),
                            tablefmt=TABULATE_FORMAT[output_format])
        else:
            return tabulate(((app_result.name,),), headers=("Application",),
                            tablefmt=TABULATE_FORMAT[output_format])


def format_package(pkg_result, output_format="blocks"):
    """Format a package object or iterable of packages in output_format."""
    if output_format == "json":
        return json.dumps(pkg_result, cls=TDSEncoder)
    try:
        iterable = iter(pkg_result)
    except TypeError:
        iterable = False
    if not iterable and isinstance(pkg_result, Exception):
        return format_exception(pkg_result)
    if output_format == "blocks":
        if iterable:
            return reduce(lambda x, y: x + '\n\n' + y,
                          (format_package(p, "blocks")
                           if not isinstance(p, Exception)
                           else format_exception(p) for p in pkg_result), "")
        else:
            return PACKAGE_TEMPLATE.format(self=pkg_result)
    else:
        if iterable:
            return tabulate(tuple((pkg.name, pkg.version, pkg.revision) for
                                  pkg in pkg_result),
                            headers=('Project', 'Version', 'Revision'),
                            tablefmt=TABULATE_FORMAT[output_format])
        else:
            return tabulate(((pkg_result.name, pkg_result.version,
                             pkg_result.revision),),
                            headers=('Project', 'Version', 'Revision'),
                            tablefmt=TABULATE_FORMAT[output_format])


def format_deployments(deployments):
    """Format a list of deployments."""
    output = []
    for pkg_dep_info in sorted(deployments,
                               key=lambda entry: entry['package'].name):
        pkg_info = {
            'pkg_def': pkg_dep_info['package'],
            'environment': pkg_dep_info['environment'],
        }

        if pkg_dep_info['by_apptype']:
            for target in sorted(pkg_dep_info['by_apptype'],
                                 key=lambda entry: entry['apptype'].name):
                # TODO: Add header for package/apptype notification
                if target['current_app_deployment'] is not None:
                    curr_app_dep = target['current_app_deployment']
                    output.append(APP_DEPLOY_HEADER_TEMPLATE.format(
                        app_dep=curr_app_dep
                    ))
                    output.append(APP_DEPLOY_TEMPLATE.format(
                        app_dep=curr_app_dep
                    ))

                    if target['previous_app_deployment'] is not None:
                        prev_app_dep = target['previous_app_deployment']
                        output.append(
                            APP_DEPLOY_TEMPLATE.format(app_dep=prev_app_dep)
                        )
                else:
                    output.append(APP_DEPLOY_MISSING_TEMPLATE.format(
                        app_dep=pkg_info
                    ))

                if target['host_deployments']:
                    output.append(HOST_DEPLOY_HEADER_TEMPLATE.format(
                        host_dep=pkg_info
                    ))

                    for host_dep in target['host_deployments']:
                        output.append(HOST_DEPLOY_TEMPLATE.format(
                            host_dep=host_dep
                        ))
        else:
            output.append(PKG_DEPLOY_MISSING_TEMPLATE.format(
                pkg_dep=pkg_info
            ))

    return '\n\n'.join(output) + '\n'


class CLI(Base):
    """
    View implementation to print to sys.stdout
    """
    def generate_result(self, view_name, tds_result):
        """
        Dispatches on the various keys in 'tds_result' to provide
        user feedback.
        """
        handler = getattr(
            self,
            'generate_%s_result' % view_name,
            self.generate_default_result
        )
        try:
            return handler(**tds_result)
        except NotImplementedError:
            print (
                "View %r not implemented (result=%r)" %
                (view_name, tds_result)
            )

    def generate_default_result(self, **kwds):
        """This is called if no matching handler is found."""
        if kwds.get('error'):
            print format_exception(kwds['error'])
        else:
            raise NotImplementedError

    def generate_project_list_result(self, result=None, error=None, **_kwds):
        """
        Show the view for a list of project objects.
        """
        if result is None and error is not None:
            result = [error]

        print format_project(result, self.output_format)

    @staticmethod
    def generate_project_delete_result(result=None, error=None, **_kwds):
        """Render view for a deleted project."""
        if result:
            print (
                'Project "%(name)s" was successfully deleted.'
                % dict(name=result.name)
            )
        elif error is not None:
            print format_exception(error)

    def generate_project_add_result(self, result=None, error=None, **_kwds):
        """Render view for a created project."""
        if result:
            if self.output_format == "blocks":
                print 'Created %(name)s:' % dict(name=result.name)
            print format_project(result, self.output_format)
        elif error:
            print format_exception(error)

    def generate_application_list_result(
            self, result=None, error=None, **_kwds
    ):
        """Render view for a list of applications."""
        if result is None and error is not None:
            result = [error]

        print format_application(result, self.output_format)

    def generate_application_update_result(
            self, result=None, error=None, **_kwds
    ):
        """Render view for an update of an application."""
        if result is None and error is not None:
            print format_exception(error)
        else:
            print format_application(result, self.output_format)
            print "Application has been successfully updated."

    @staticmethod
    def generate_application_delete_result(result=None, error=None, **_kwds):
        """Render view for a deleted application."""
        if result:
            print (
                'Application "%(name)s" was successfully deleted.'
                % dict(name=result.name)
            )
        elif error is not None:
            print format_exception(error)

    def generate_application_add_result(self, result=None, error=None,
                                        **_kwds):
        """Render view for a created application."""
        if result:
            if self.output_format == "blocks":
                print 'Created %(name)s:' % dict(name=result.name)
            print format_application(result, self.output_format)
        elif error:
            print format_exception(error)

    def generate_application_add_apptype_result(
        self, result=None, error=None, **kwds
    ):
        """Format the result of an "application add-apptype" action."""
        if error is not None:
            return self.generate_default_result(
                result=result, error=error, **kwds
            )

        print (
            ('Future deployments of "%(application)s" in "%(project)s" '
             'will affect %(names)s')
            % dict(
                project=result['project'],
                application=result['application'],
                names=', '.join('"%s"' % x for x in result['targets'])
            )
        )

    def generate_application_delete_apptype_result(
        self, result=None, error=None, **kwds
    ):
        """Format the result of an "application delete-apptype" action."""
        if error is not None:
            return self.generate_default_result(
                result=result, error=error, **kwds
            )

        print (
            ('Future deployments of "%(application)s" in "%(project)s" '
             'will no longer affect "%(name)s"')
            % dict(
                application=result['application'].name,
                project=result['project'].name,
                name=result['target'].name
            )
        )

    @staticmethod
    def generate_deploy_show_result(result=None, error=None, **_kwds):
        """Render view for a list of deployments."""
        if result is not None:
            print format_deployments(result)
        elif error:
            print format_exception(error)

    def generate_package_add_result(self, result=None, error=None, **kwds):
        """Format the result of a "package add" action."""
        if error is not None:
            return self.generate_default_result(
                result=result, error=error, **kwds
            )

        package = result['package']
        print (
            'Added package: "%s@%s"' % (package.name, package.version)
        )

    def generate_package_list_result(self, result=None, error=None, **kwds):
        """
        Generate the package list display for the given results, which
        should be an iterable with items that satisfy the
        PACKAGE_TEMPLATE above.
        """
        if error is not None:
            return self.generate_default_result(
                result=result, error=error, **kwds
            )

        print format_package(result, self.output_format)

    def generate_deploy_restart_result(self, result=None, error=None, **kwds):
        """Format the result of a "deploy restart" action."""
        if error is not None:
            return self.generate_default_result(
                result=result, error=error, **kwds
            )

        keys = sorted(result.keys())
        printed_fail_message = False
        for key in keys:
            if not result[key]:
                if not printed_fail_message:
                    print "Some hosts had failures:\n"
                    printed_fail_message = True
                host, pkg = key
                print "%s (%s)" % (host.name, pkg.name)

    generate_deploy_invalidate_result = \
        generate_deploy_promote_result = \
        generate_deploy_validate_result = \
        generate_deploy_rollback_result = \
        generate_deploy_fix_result = \
        silence(NotImplementedError)(generate_default_result)
