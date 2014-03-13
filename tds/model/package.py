import tagopsdb.database.model as model

class Package(object):
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

    def __eq__(self, other):
        return self.__dict__.__eq__(other.__dict__)
