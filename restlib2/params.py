import logging
from functools import partial

logger = logging.getLogger(__name__)


class Param(object):
    "Describes a single parameter and defines a method for cleaning inputs."
    def __init__(self, default=None, allow_list=False, description=None, param_key=None, choices=None, **kwargs):
        self.default = default
        self.allow_list = allow_list
        self.description = description
        self.param_key = param_key
        self.choices = choices

        for key in kwargs:
            setattr(self, key, kwargs[key])

    def clean(self, value, *args, **kwargs):
        if self.choices and value not in self.choices:
            raise ValueError
        return value

    def clean_list(self, values, *args, **kwargs):
        return map(lambda x: self.clean(x, *args, **kwargs), values)


class IntParam(Param):
    def clean(self, value, *args, **kwargs):
        return super(IntParam, self).clean(int(value), *args, **kwargs)


class FloatParam(Param):
    def clean(self, value, *args, **kwargs):
        return super(FloatParam, self).clean(float(value), *args, **kwargs)


class StrParam(Param):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('strip', True)
        super(StrParam, self).__init__(*args, **kwargs)

    def clean(self, value, *args, **kwargs):
        value = str(value)
        if self.strip:
            value = value.strip()
        return super(StrParam, self).clean(value, *args, **kwargs)


class UnicodeParam(StrParam):
    def clean(self, value, *args, **kwargs):
        value = unicode(value)
        if self.strip:
            value = value.strip()
        return super(UnicodeParam, self).clean(value, *args, **kwargs)


class BoolParam(Param):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('true_values', ('t', 'true', '1', 'yes'))
        kwargs.setdefault('false_values', ('f', 'false', '0', 'no'))
        super(BoolParam, self).__init__(*args, **kwargs)

    def clean(self, value, *args, **kwargs):
        value = value.lower()
        if value in self.true_values:
            value = True
        elif value in self.false_values:
            value = False
        else:
            raise ValueError
        return super(BoolParam, self).clean(value, *args, **kwargs)


class ParametizerMetaclass(type):
    def __new__(cls, name, bases, attrs):
        new_cls = type.__new__(cls, name, bases, attrs)

        if hasattr(new_cls, 'param_defaults'):
            defaults = new_cls.param_defaults.copy()
        else:
            defaults = {}

        fields = {}

        for attr, value in attrs.items():
            if not callable(value) and not attr.startswith('__'):
                # Wrap shorthand definition in param class
                if isinstance(value, Param):
                    field = value
                    key = field.param_key or attr
                    value = field.default
                else:
                    key = attr
                    field = Param(default=value)
                    clean_method = 'clean_{0}'.format(attr)
                    # Partially apply the clean method with the field as self
                    if clean_method in attrs:
                        field.clean = partial(attrs[clean_method], field)

                fields[key] = field
                defaults[key] = value

        new_cls._fields = fields
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

            # Get associated param instance or initialize default one
            field = self._fields.get(key, Param())

            # Support MultiValueDict (request.GET and POST)
            if field.allow_list and hasattr(params, 'getlist'):
                value = params.getlist(key)
            else:
                value = params.get(key)

            # If any kind of error occurs while cleaning, revert to
            # the default value
            try:
                if isinstance(value, (list, tuple)):
                    value = field.clean_list(value)
                    if not field.allow_list:
                        value = value[0]
                else:
                    value = field.clean(value)
            except Exception as e:
                logger.debug('Error cleaning parameter', extra={
                    'key': key,
                    'value': value,
                })
                value = defaults.get(key, value)

            cleaned[key] = value

        return cleaned


# Backwards compatibility
class ParamCleaners(object):
    "Container of various common cleaners for parameters."
    clean_int = IntParam().clean
    clean_float = FloatParam().clean
    clean_string = StrParam().clean
    clean_bool = BoolParam().clean


param_cleaners = ParamCleaners()
