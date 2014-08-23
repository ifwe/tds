'''
A command line view for TDS
'''
from .base import Base


# TODO: this isn't planned out AT ALL
PROJECT_TEMPLATE = (
    'Project: {self.name}\n'
    'Environment Specific: {self.environment_specific}\n'
    # 'Project type: {self.type}\n'
)
APP_TEMPLATE = (
    'Application name: {self.pkg_name}\n'
    'Path: {self.path}\n'
    'Build host: {self.build_host}\n'
    'Environment Specific: {self.environment_specific}\n'
)
TARGET_TEMPLATE = ('App types: {s}\n')
APP_DEPLOY_HEADER_TEMPLATE = (
    'Deployment of {self.deployment.package.name} '
    'to {self.application.name} tier '
    'in {self.environment} environment:\n'
    '==========\n'
)
APP_DEPLOY_MISSING_TEMPLATE = (
    'No deployments to tiers for {self[pkg_def].name} '
    '(for possible given version) yet '
    'in {self[environment]} environment\n'
)
APP_DEPLOY_TEMPLATE = (
    'Version: {self.deployment.package.version}-'
    '{self.deployment.package.revision}\n'
    'Declared: {self.deployment.declared}\n'
    'Declaring user: {self.deployment.user}\n'
    'Realized: {self.realized}\n'
    'Realizing user: {self.user}\n'
    'App type: {self.application.name}\n'
    'Environment: {self.environment}\n'
    'Deploy state: {self.deployment.dep_type}\n'
    'Install state: {self.status}\n'
)
HOST_DEPLOY_HEADER_TEMPLATE = (
    'Deployment of {self.deployment.package.name} to hosts '
    'in {self.environment} environment:\n'
    '==========\n'
)
HOST_DEPLOY_MISSING_TEMPLATE = (
    'No deployments to hosts for {self[pkg_def].name} '
    '(for possible given version) '
    'in {self[environment]} environment\n'
)
HOST_DEPLOY_TEMPLATE = (
    'Version: {self.deployment.package.version}-'
    '{self.deployment.package.revision}\n'
    'Declared: {self.deployment.declared}\n'
    'Declaring user: {self.deployment.user}\n'
    'Realized: {self.realized}\n'
    'Realizing user: {self.user}\n'
    'Hostname: {self.host_id}\n'
    'Deploy state: {self.deployment.dep_type}\n'
    'Install state: {self.status}\n'
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

def format_access_error(exc):
    return (
        'Your account does not have the appropriate '
        'permissions to run the requested command.'
    )


def format_exception_default(exc):
    return exc.args[0] % exc.args[1:]


def format_project(project):
    'Format a project object'
    output = []
    output.append(PROJECT_TEMPLATE.format(self=project))
    output.append(TARGET_TEMPLATE.format(
        s=', '.join(x.app_type.encode('utf8') for x in project.targets)
    ))
    for app in project.applications:
        app_result = []
        app_info = APP_TEMPLATE.format(self=app)
        app_result.extend(app_info.splitlines())
        output.append('\n\t'.join(app_result))

    return ''.join(output) + '\n'


def format_deployments(deployments):
    'Format a list of deployments'
    output = []
    for pkg_dep_info in deployments:
        no_dep = {
            'pkg_def': pkg_dep_info['package'],
            'environment': pkg_dep_info['environment'],
        }

        if pkg_dep_info['by_apptype']:
            for target in pkg_dep_info['by_apptype']:
                if target['current_deployment'] is not None:
                    curr_dep = target['current_deployment']
                    output.append(
                        APP_DEPLOY_HEADER_TEMPLATE.format(self=curr_dep)
                    )
                    output.append(APP_DEPLOY_TEMPLATE.format(self=curr_dep))
                else:
                    output.append(APP_DEPLOY_MISSING_TEMPLATE.format(
                        self=no_dep
                    ))
                    continue

                if target['previous_deployment'] is not None:
                    prev_dep = target['previous_deployment']
                    output.append(
                        APP_DEPLOY_TEMPLATE.format(self=prev_dep)
                    )
        else:
            output.append(APP_DEPLOY_MISSING_TEMPLATE.format(self=no_dep))

        if pkg_dep_info['by_hosts']:
            for target in pkg_dep_info['by_hosts']:
                if target['deployment'] is not None:
                    host_dep = target['deployment']
                    output.append(
                        HOST_DEPLOY_HEADER_TEMPLATE.format(self=host_dep)
                    )
                    output.append(HOST_DEPLOY_TEMPLATE.format(self=host_dep))
                else:
                    output.append(
                        HOST_DEPLOY_MISSING_TEMPLATE.format(self=no_dep)
                    )
        else:
            output.append(
                HOST_DEPLOY_MISSING_TEMPLATE.format(self=no_dep)
            )

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

    @staticmethod
    def generate_default_result(**kwds):
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
            print 'Could not delete: %(message)s' % dict(
                message=format_exception(error)
            )

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

    @classmethod
    def generate_deploy_add_apptype_result(cls,
        result=None, error=None, **kwds
    ):
        'Format the result of a "deploy add-apptype" action'
        if error is not None:
            return cls.generate_default_result(
                result=result, error=error, **kwds
            )

        print (
            'Future deployments of "%(project)s" will affect "%(target)s"'
            % result
        )

    @classmethod
    def generate_deploy_delete_apptype_result(cls,
        result=None, error=None, **kwds
    ):
        'Format the result of a "deploy delete-apptype" action'
        if error is not None:
            return cls.generate_default_result(
                result=result, error=error, **kwds
            )

        print (
            ('Future deployments of "%(project)s" will no longer '
                'affect "%(target)s"')
            % result
        )

    @classmethod
    def generate_package_add_result(cls, result=None, error=None, **kwds):
        'Format the result of a "package add" action'
        if error is not None:
            return cls.generate_default_result(
                result=result, error=error, **kwds
            )

        package = result['package']
        print (
            'Added package version: "%s@%s"' % (package.name, package.version)
        )

    @classmethod
    def generate_deploy_restart_result(cls, result=None, error=None, **kwds):
        'Format the result of a "deploy restart" action'
        if error is not None:
            return cls.generate_default_result(
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
                print "%s (%s)" % host.name, pkg.name

