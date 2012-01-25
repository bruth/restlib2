from .structures import LookupDict

_methods = (
    'OPTIONS',
    'HEAD',
    'GET',
    'POST',
    'DELETE',
    'PATCH',
    'TRACE',
)

methods = LookupDict(name='methods')

for method in _methods:
    setattr(methods, method, method)
    setattr(methods, method.lower(), method)
