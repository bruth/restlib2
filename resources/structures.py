class NameDescriptor(object):
    def __set__(self, instance, value):
        self.name = value

    def __get__(self, instance, owner):
        return self.name


class AttrDict(object):
    "A named attribute accessible dict-like object"
    name = NameDescriptor()

    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.__dict__.update(*args, **kwargs)

    def __repr__(self):
        return u'<AttrDict: %s>' % self.name

    def __getattr__(self, key):
        return self.__dict__.get(key.upper(), None)

    def __contains__(self, key):
        return self.__dict__.__contains__(key.upper())

    def __iter__(self):
        return self.__dict__.__iter__()

