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

        cleaned = {}

        # Gather both sets of keys since there may be methods defined
        # without a default value specified.
        keys = set(defaults.keys() + params.keys())

        for key in keys:
            # Add the default value for non-existant keys in params
            if key not in params:
                cleaned[key] = defaults[key]
                continue

            method = 'clean_{0}'.format(key)

            value = params[key]

            # Attempt to clean the value
            if hasattr(self, method):
                cleaner = getattr(self, method)

                # If any kind of error occurs while cleaning, revert to
                # the default value
                try:
                    # Unpack single item lists
                    if isinstance(value, (list, tuple)):
                        value = map(cleaner, value)
                    else:
                        value = cleaner(value)
                except Exception:
                    value = defaults.get(key, value)

            # Unpack single values
            if isinstance(value, (list, tuple)) and len(value) == 1:
                value = value[0]

            cleaned[key] = value

        return cleaned


class ParamCleaners(object):
    "Container of various common cleaners for parameters."

    def clean_int(self, value):
        return int(value)

    def clean_float(self, value):
        return float(value)

    def clean_string(self, value):
        return value.strip()

    def clean_bool(self, value):
        value = value.lower()
        if value in ('t', 'true', '1', 'yes'):
            return True
        if value in ('f', 'false', '0', 'no'):
            return False
        raise ValueError


param_cleaners = ParamCleaners()
