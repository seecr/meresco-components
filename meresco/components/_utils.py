
class Bucket(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def get(self, key, default):
        return self.__dict__.get(key, default)

    def __repr__(self):
        return simplerepr(self)

def simplerepr(o):
    return '%s(%s)' % (o.__class__.__name__, ', '.join("%s=%s" % (key, repr(value)) for key, value in o.__dict__.items()))

__all__ = ['simplerepr', 'Bucket']
