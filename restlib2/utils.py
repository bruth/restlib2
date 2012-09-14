import warnings
from preserialize.serialize import serialize
warnings.warn('The `serialize` method has been removed from restlib2 core ' \
    'and uses the django-preserialize library instead. Replace any imports ' \
    'of `restlib.utils.serialize` to `preserialize.serialize.serialize`.',
    DeprecationWarning)
