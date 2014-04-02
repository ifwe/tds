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
    def generate_projects_result(result=None, error=None, **kwds):
        '''
        Show the view for a list of project objects
        '''
        output = []
        for project in result:
            output.append(PROJECT_TEMPLATE.format(self=project))
            for app in project.applications:
                app_result = []
                app_info = APP_TEMPLATE.format(self=app)
                app_result.extend(app_info.splitlines())
                target_group_info = TARGET_TEMPLATE.format(
                    s=repr([x.encode('utf8') for x in app.target_groups])
                )
                app_result.append(target_group_info)
                output.append('\n\t'.join(app_result))
            output.append('\n')
        print ''.join(output)
