'''Base module for TDS objects'''

class Base(object):
    'Base class for TDS objects'
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

    def __eq__(self, other):
        return self.__dict__.__eq__(other.__dict__)
