'''Base module for TDS objects'''


class Base(object):
    'Base class for TDS objects'
    delegate = None

    def __init__(self, **kwds):
        self.__dict__.update(kwds)

    def __eq__(self, other):
        return self.__dict__.__eq__(other.__dict__)

    def __repr__(self):
        return '<%(class_name)s %(fields_str)s>' % dict(
            class_name=type(self).__name__,
            fields_str=' '.join('%s=%r' % i for i in vars(self).items()),
        )

    @classmethod
    def from_db(cls, row):
        raise NotImplementedError

    @classmethod
    def all(cls, **kwds):
        'Return all instances of this class'
        return map(cls.from_db, cls.delegate.all(**kwds))

    @classmethod
    def find(cls, **kwds):
        'Return all instances of this class matching kwds'
        rows = cls.delegate.find(**kwds)
        return map(cls.from_db, rows)

    @classmethod
    def get(cls, **kwds):
        'Return the first instance of this class matching kwds'
        raise NotImplementedError

    @classmethod
    def get_by(cls, *a, **k):
        row = cls.delegate.get_by(*a, **k)
        if row is None:
            return None
        return cls.from_db(row)
