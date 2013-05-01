def clean_bool(value, allow_none=False):
    if isinstance(value, bool):
        return value

    if isinstance(value, basestring):
        value = value.lower()
        if value in ('t', 'true', '1', 'yes'):
            return True
        if value in ('f', 'false', '0', 'no'):
            return False
    if allow_none and value is None:
        return
    raise ValueError


class ParametizerMetaclass(type):
    def __new__(cls, name, bases, attrs):
        new_cls = type.__new__(cls, name, bases, attrs)  

        if hasattr(new_cls, 'param_defaults'):
            defaults = new_cls.param_defaults.copy()
        else:
            defaults = {}

        for key, value in attrs.items():
            if not callable(value) and not key.startswith('__'):
                defaults[key] = value

        new_cls.param_defaults = defaults

        return new_cls


class Parametizer(object):
    __metaclass__ = ParametizerMetaclass
    
    def clean(self, params=None, defaults=None):
        if params is None:
            params = {}

        if defaults is None:
            defaults = self.param_defaults

        cleaned = defaults.copy()
        cleaned.update(params)

        for key in cleaned:
            method = 'clean_{0}'.format(key)
            if hasattr(self, method):
                value = cleaned[key]
                cleaner = getattr(self, method)
                
                # If any kind of error occurs while cleaning, revert to
                # the default value
                try:
                    # Unpack single item lists
                    if isinstance(value, (list, tuple)):
                        value = map(cleaner, value)
                        if len(value) == 1:
                            value = value[0]
                    else:
                        value = cleaner(value)
                except Exception:
                    value = defaults.get(key)

                cleaned[key] = value

        return cleaned
