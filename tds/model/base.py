'''Base module for TDS objects'''
import tagopsdb


class _Base(object):
    'base class for Base to absorb all kwds'
    def __init__(self, **_kwds):
        super(_Base, self).__init__()

class Base(_Base):
    'Base class for TDS objects'

    def __init__(self, **kwds):
        for key, val in kwds.iteritems():
            setattr(self, key, val)

        super(Base, self).__init__(**kwds)

    def __eq__(self, other):
        return self.__dict__.__eq__(other.__dict__)

    def __repr__(self):
        return '<%(class_name)s %(fields_str)s>' % dict(
            class_name=type(self).__name__,
            fields_str=' '.join('%s=%r' % i for i in vars(self).items()),
        )

    def delete(self, commit=True, *args, **kwargs):
        'Delete action with default auto-commit'
        super(Base, self).delete(*args, **kwargs)
        if commit:
            tagopsdb.Session.commit()

    @classmethod
    def create(cls, commit=True, **kwargs):
        'Create action with default auto-commit'
        self = cls(**kwargs)
        tagopsdb.Session.add(self)
        if commit:
            tagopsdb.Session.commit()
        return self
