'''Base module for TDS objects'''
import tagopsdb


class Base(object):
    'Base class for TDS objects'

    def __init__(self, **kwds):
        super(Base, self).__init__(**kwds)

    def __eq__(self, other):
        return self.__dict__.__eq__(other.__dict__)

    # def __repr__(self):
    #     return '<%(class_name)s %(fields_str)s>' % dict(
    #         class_name=type(self).__name__,
    #         fields_str=' '.join('%s=%r' % i for i in vars(self).items()),
    #     )

    def delete(self, commit=True, *args, **kwargs):
        super(Base, self).delete(*args, **kwargs)
        if commit:
            tagopsdb.Session.commit()

    @classmethod
    def create(cls, commit=True, **kwargs):
        self = cls(**kwargs)
        tagopsdb.Session.add(self)
        if commit:
            tagopsdb.Session.commit()
        return self
