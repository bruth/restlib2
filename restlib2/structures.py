import re

try:
    str = unicode
except NameError:
    pass


class AttrDict(object):
    "A case-insensitive attribute accessible dict-like object"
    def __init__(self, name, *args, **kwargs):
        self.name = name

        for key, value in dict(*args, **kwargs).items():
            if not isinstance(key, (str, bytes)) or not key:
                raise TypeError('attribute names must be non-empty strings')
            if key[0].isdigit():
                raise ValueError('attribute names cannot begin with a number')
            _key = re.sub(r'[^\w\d_]+', ' ', re.sub(r'[\s-]+', '_', str(key).upper()))
            self.__dict__[_key] = value

    def __repr__(self):
        return '<AttrDict: %s>' % self.name

    def __getattr__(self, key):
        _key = key.upper()
        if _key not in self.__dict__:
            raise AttributeError("AttrDict object has not attribute '{0}'".format(key))
        return self.__dict__[_key]

    def __contains__(self, key):
        return self.__dict__.__contains__(key.upper())

    def __iter__(self):
        return self.__dict__.__iter__()
