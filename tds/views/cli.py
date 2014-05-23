'''
A command line view for TDS
'''
from .base import Base


# TODO: this isn't planned out AT ALL
PROJECT_TEMPLATE = (
    'Project: {self.name}\n'
    # 'Project type: {self.type}\n'
)
APP_TEMPLATE = (
    'Application name: {self.name}\n'
    'Path: {self.path}\n'
    'Build host: {self.build_host}\n'
    'Environment Specific: {self.environment_specific}\n'
)
TARGET_TEMPLATE = ('App types: {s}\n')

def format_project(project):
    output = []
    output.append(PROJECT_TEMPLATE.format(self=project))
    for app in project.applications:
        app_result = []
        app_info = APP_TEMPLATE.format(self=app)
        app_result.extend(app_info.splitlines())
        target_group_info = TARGET_TEMPLATE.format(
            s=', '.join(x.encode('utf8') for x in app.target_groups)
        )
        app_result.append(target_group_info)
        output.append('\n\t'.join(app_result))
    output.append('\n')

    return ''.join(output)

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
        return handler(**tds_result)

    @staticmethod
    def generate_default_result(**kwds):
        raise NotImplementedError

    @staticmethod
    def generate_project_list_result(result=None, **kwds):
        '''
        Show the view for a list of project objects
        '''
        output = []
        for project in result:
            output.append(format_project(project))
        print ''.join(output)

    @staticmethod
    def generate_project_delete_result(result=None, error=None, **kwds):
        if result:
            print '%(name)s was successfully deleted.' % dict(name=result.name)
        elif error:
            message, name = error.args[:2]
            print 'Could not delete %(name)s: %(message)s' % dict(name=name, message=message)
            raise error

    @staticmethod
    def generate_project_create_result(result=None, error=None, **kwds):
        if result:
            print 'Created %(name)s:' % dict(name=result.name)
            print format_project(result)
        elif error:
            message, name = error.args[:2]
            print 'Could not create %(name)s: %(message)s' % dict(name=name, message=message)
