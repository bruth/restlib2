from django.db import models
from django.db.models.query import QuerySet

PSEUDO_SELECTORS = (':all', ':pk', ':local', ':related')
DEFAULT_SELECTORS = (':pk', ':local')

def convert_to_camel(s):
    if '_' not in s:
        return s
    toks = s.split('_')
    return toks[0] + ''.join(x.title() for x in toks[1:] if x.upper() != x)


class ModelFieldResolver(object):
    cache = {}

    def _get_pk_field(self, model):
        fields = (model._meta.pk,)
        names = tuple(map(lambda x: x.name, fields))

        return {
            ':pk': dict(zip(names, fields)),
        }

    def _get_local_fields(self, model):
        "Return the names of all locally defined fields on the model class."
        local = model._meta.fields
        m2m = model._meta.many_to_many

        fields = local + m2m
        names = tuple(map(lambda x: x.name, fields))

        return {
            ':local': dict(zip(names, fields)),
        }

    def _get_related_fields(self, model):
        "Returns the names of all related fields for model class."
        reverse_fk = model._meta.get_all_related_objects()
        reverse_m2m = model._meta.get_all_related_many_to_many_objects()

        fields = tuple(reverse_fk + reverse_m2m)
        names = tuple(map(lambda x: x.get_accessor_name(), fields))

        return {
            ':related': dict(zip(names, fields)),
        }

    def _get_fields(self, model):
        if not self.cache.has_key(model):
            fields = {}

            fields.update(self._get_pk_field(model))
            fields.update(self._get_local_fields(model))
            fields.update(self._get_related_fields(model))

            all_ = {}
            for x in fields.values():
                all_.update(x)

            fields[':all'] = all_

            self.cache[model] = fields

        return self.cache[model]

    def get_field(self, model, attr):
        fields = self._get_fields(model)

        # Alias to model fields
        if attr in PSEUDO_SELECTORS:
            return fields[attr].keys()

        # Assume a field or property
        return attr

resolver = ModelFieldResolver()

def parse_selectors(model, fields=None, exclude=None, key_map=None, **options):
    """Validates fields are valid and maps pseudo-fields to actual fields
    for a given model class.
    """
    fields = fields or DEFAULT_SELECTORS
    exclude = exclude or ()
    key_map = key_map or {}
    validated = []

    for alias in fields:
        # Map the output key name to the actual field/accessor name for
        # the model
        actual = key_map.get(alias, alias)

        # Validate the field exists
        cleaned = resolver.get_field(model, actual)

        if cleaned is None:
            raise AttributeError('The "{0}" attribute could not be found '
                'on the model "{1}"'.format(actual, model))

        # Mapped value, so use the original name listed in `fields`
        if type(cleaned) is list:
            validated.extend(cleaned)
        elif alias != actual:
            validated.append(alias)
        else:
            validated.append(cleaned)

    return tuple([x for x in validated if x not in exclude])


def get_field_value(obj, name):
    if hasattr(obj, name):
        value = getattr(obj, name)
    elif hasattr(obj, '__getitem__'):
        value = obj[name]
    else:
        raise ValueError('{} has not attribute {}'.format(obj, name))

    # Check for callable
    if callable(value):
        value = value()

    # Handle a local many-to-many or a reverse foreign key
    elif value.__class__.__name__ in ('RelatedManager', 'ManyRelatedManager',
            'GenericRelatedObjectManager'):
        value = value.all()

    return value

def obj_to_dict(obj, fields, **options):
    """Takes a model object or queryset and converts it into a native object
    given the list of attributes either local or related to the object.
    """
    obj_dict = {}
    related = options.get('related', {})
    key_map = options.get('key_map', {})
    camelcase = options['camelcase']
    prefix = options.get('key_prefix', '')

    for alias in fields:
        actual = key_map.get(alias, alias)
        # Create the key that will be used in the output dict
        key = camelcase(prefix + alias)

        # Get the field value. Use the mapped value to the actually property or
        # method name. `value` may be a number of things, so the various types
        # are checked below.
        value = get_field_value(obj, actual)

        # Related objects, perform some checks on their options
        if isinstance(value, (models.Model, QuerySet)):
            rel_options = related.get(actual, {})
            # Propagate `camelcase` option by default
            rel_options.setdefault('camelcase', camelcase)

            rel_prefix = rel_options.get('key_prefix', '')

            # If the `key_prefix` follows the below template, generate the
            # `key_prefix` for the related object
            if rel_prefix and '%(accessor)s' in rel_prefix:
                rel_options['key_prefix'] = rel_prefix % {'accessor': alias}

            if isinstance(value, models.Model):
                # Recursve, get the dict representation
                rel_obj_dict = serialize(value, **rel_options)

                # Check if this object should be merged into the parent object,
                # otherwise nest it under the accessor name
                if rel_options.get('merge', False):
                    obj_dict.update(rel_obj_dict)
                else:
                    obj_dict[key] = rel_obj_dict
            else:
                obj_dict[key] = serialize(value, **rel_options)
        else:
            obj_dict[key] = value

    return obj_dict


def queryset_to_list(queryset, fields, **options):
    # If the `select_related` option is defined, update the `QuerySet`
    if 'select_related' in options:
        queryset = queryset.select_related(*options['select_related'])

    if options.get('values_list', False):
        # Flatten if only one field is being selected
        if len(fields) == 1:
            flat = options.get('flat', True)
            queryset = queryset.values_list(fields[0], flat=flat)
        else:
            queryset = queryset.values_list(*fields)
        return list(queryset)

    return map(lambda x: obj_to_dict(x, fields, **options),
            queryset.iterator())


def serialize(obj, fields=None, exclude=None, **options):
    """Recursively attempts to find ``Model`` and ``QuerySet`` instances
    to convert them into their representative datastructure per their
    ``Resource`` (if one exists).
    """
    camelcase = options.get('camelcase', False)
    # Explicit check for boolean value since during recursion, the function
    # will be propagated (if unchanged)
    if camelcase is True:
        options['camelcase'] = convert_to_camel
    elif camelcase is False:
        options['camelcase'] = lambda x: x

    # Handle model instances
    if isinstance(obj, models.Model):
        fields = parse_selectors(obj.__class__, fields, exclude, **options)
        return obj_to_dict(obj, fields, **options)

    # Handle querysets
    if isinstance(obj, QuerySet):
        fields = parse_selectors(obj.model, fields, exclude, **options)
        return queryset_to_list(obj, fields, **options)

    # Handle dict instances
    if isinstance(obj, dict):
        exclude = exclude or []
        if not fields:
            fields = obj.iterkeys()
        fields = [x for x in fields if x not in exclude]
        return obj_to_dict(obj, fields, **options)

    # Handle other iterables
    if hasattr(obj, '__iter__'):
        return map(lambda x: serialize(x, fields, exclude, **options), obj)
