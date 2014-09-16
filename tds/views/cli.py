'''
A command line view for TDS
'''
from .base import Base

def silence(*exc_classes):
    def wrap_func(f):
        def call_func(*a, **k):
            try:
                return f(*a, **k)
            except exc_classes:
                return None
        return call_func
    return wrap_func

# TODO: this isn't planned out AT ALL
PROJECT_TEMPLATE = (
    'Project: {self.name}\n'
    'Environment Specific: {self.environment_specific}\n'
    # 'Project type: {self.type}\n'
)
APP_TEMPLATE = (
    'Application name: {self.pkg_name}\n'
    'Architecture: {self.arch}\n'
    'Path: {self.path}\n'
    'Build host: {self.build_host}\n'
    'Environment Specific: {self.environment_specific}\n'
)
TARGET_TEMPLATE = ('App types: {s}\n')
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
    'Deployment of {pkg_dep[pkg_def].name} to hosts '
    'in {pkg_dep[pkg_def].environment} environment:\n'
    '==========\n'
)
# Note: the following template is unused for now and may be
#       removed in the near future
HOST_DEPLOY_MISSING_TEMPLATE = (
    'No deployments to hosts for {pkg_dep[pkg_def].name} '
    '(for possible given version) '
    'in {pkg_dep[environment]} environment\n'
)
HOST_DEPLOY_TEMPLATE = (
    'Version: {host_dep.deployment.package.version}-'
    '{host_dep.deployment.package.revision}\n'
    'Declared: {host_dep.deployment.declared}\n'
    'Declaring user: {host_dep.deployment.user}\n'
    'Realized: {host_dep.realized}\n'
    'Realizing user: {host_dep.user}\n'
    'Hostname: {host_dep.host_id}\n'
    'Deploy state: {host_dep.deployment.dep_type}\n'
    'Install state: {host_dep.status}\n'
)

PACKAGE_TEMPLATE = (
    'Project: {self.name}\n'
    'Version: {self.version}\n'
    'Revision: {self.revision}\n'
)


def format_access_error(exc):
    return (
        'You do not have the appropriate permissions to run this command. '
        'Contact your manager.'
    )


EXCEPTION_FORMATTERS = dict(
    AccessError=format_access_error
)


def format_exception(exc):
    'Format an exception for user consumption'

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
    return exc.args[0] % exc.args[1:]


def format_project(project):
    'Format a project object'
    output = []
    output.append(PROJECT_TEMPLATE.format(self=project))
    for app in project.applications:
        app_result = []
        app_info = APP_TEMPLATE.format(self=app)
        app_result.extend(app_info.splitlines())
        app_names = set(x.name for x in project.applications)
        app_result.append(TARGET_TEMPLATE.format(
            s=', '.join(
                x.name.encode('utf8') for x in project.targets
                if set(p.name for p in x.package_definitions) & app_names
            )
        ))
        output.append('\n\t'.join(app_result))

    return ''.join(output) + '\n'


def format_package(package):
    return PACKAGE_TEMPLATE.format(self=package)


def format_deployments(deployments):
    'Format a list of deployments'
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
    '''
    View implementation to print to sys.stdout
    '''
    def generate_result(self, view_name, tds_result):
        '''
        Dispatches on the various keys in 'tds_result' to provide
        user feedback.
        '''
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
        'This is called if no matching handler is found'
        if kwds.get('error'):
            print format_exception(kwds['error'])
        else:
            raise NotImplementedError

    @staticmethod
    def generate_project_list_result(result=None, error=None, **_kwds):
        '''
        Show the view for a list of project objects
        '''
        if result is None and error is not None:
            result = [error]

        output = []
        for project in result:
            if isinstance(project, Exception):
                output.append(format_exception(project) + '\n')
            else:
                output.append(format_project(project))
        print ''.join(output)

    @staticmethod
    def generate_project_delete_result(result=None, error=None, **_kwds):
        'Render view for a deleted project'
        if result:
            print (
                'Project "%(name)s" was successfully deleted.'
                % dict(name=result.name)
            )
        elif error is not None:
            print format_exception(error)

    @staticmethod
    def generate_project_create_result(result=None, error=None, **_kwds):
        'Render view for a created project'
        if result:
            print 'Created %(name)s:' % dict(name=result.name)
            print format_project(result)
        elif error:
            print format_exception(error)

    @staticmethod
    def generate_deploy_show_result(result=None, error=None, **_kwds):
        'Render view for a list of deployments'
        if result is not None:
            print format_deployments(result)
        elif error:
            print format_exception(error)

    def generate_deploy_add_apptype_result(self,
        result=None, error=None, **kwds
    ):
        'Format the result of a "deploy add-apptype" action'
        if error is not None:
            return self.generate_default_result(
                result=result, error=error, **kwds
            )

        print (
            'Future deployments of "%(project)s" will affect "%(target)s"'
            % result
        )

    def generate_deploy_delete_apptype_result(self,
        result=None, error=None, **kwds
    ):
        'Format the result of a "deploy delete-apptype" action'
        if error is not None:
            return self.generate_default_result(
                result=result, error=error, **kwds
            )

        print (
            ('Future deployments of "%(project)s" will no longer '
                'affect "%(target)s"')
            % result
        )

    def generate_package_add_result(self, result=None, error=None, **kwds):
        'Format the result of a "package add" action'
        if error is not None:
            return self.generate_default_result(
                result=result, error=error, **kwds
            )

        package = result['package']
        print (
            'Added package version: "%s@%s"' % (package.name, package.version)
        )

    def generate_package_list_result(self, result=None, error=None, **kwds):
        if error is not None:
            return self.generate_default_result(
                result=result, error=error, **kwds
            )

        package_texts = []
        for package in result:
            package_texts.append(format_package(package))

        print '\n\n'.join(package_texts)

    def generate_deploy_restart_result(self, result=None, error=None, **kwds):
        'Format the result of a "deploy restart" action'
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
    generate_deploy_redeploy_result = \
    silence(NotImplementedError)(generate_default_result)
