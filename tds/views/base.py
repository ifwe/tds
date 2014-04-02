'''
Base class and helpers for tds.views
'''


class Base(object):
    'Base class and interface for a tds.views class'
    def generate_result(self, tds_result):
        '''
        Create something useful for the user which will be returned
        to the main application entry point.
        '''
        raise NotImplementedError
