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

        # Model field
        elif attr in fields[':all']:
            return attr

        # Property or method
        elif hasattr(model, attr):
            return attr


resolver = ModelFieldResolver()

def parse_selectors(model, fields=None, exclude=None):
    """Recursively verifies all of ``attrs`` for the given model (and related
    models) exist. It also substitutes any pseduo-selectors present with the
    attribute names.
    """
    fields = fields or DEFAULT_SELECTORS
    exclude = exclude or ()
    level = []

    for name in fields:
        # This implies traversing through a related object, this will be
        # parsed later
        if isinstance(name, dict):
            level.append(name)
            continue

        attr = resolver.get_field(model, name)

        if attr is None:
            raise AttributeError('The "%s" attribute could not be found '
                'on the model "%s"' % (name, model))

        if type(attr) is list:
            level.extend(attr)
        else:
            level.append(attr)

    return tuple([x for x in level if x not in exclude])


def get_field_value(obj, name): 
    value = getattr(obj, name)

    # Check for callable
    if callable(value):
        value = value()

    # Handle a local many-to-many or a reverse foreign key
    elif value.__class__.__name__ in ('RelatedManager', 'ManyRelatedManager', 'GenericRelatedObjectManager'):
        value = value.all()

    return value

def model_to_dict(obj, fields=None, exclude=None, related=None, **options):
    """Takes a model object or queryset and converts it into a native object
    given the list of attributes either local or related to the object.
    """
    obj_dict = {}
    keymap = options['keymap']
    camelize = options['camelize']
    related = related or {}

    # Define prefix
    prefix = options.get('key_prefix', '')

    fields = parse_selectors(obj.__class__, fields, exclude)

    for name in fields:
        rel_options = {}

        key = prefix + name
        # Get the field value, this may be a number of things
        value = get_field_value(obj, name)

        # Foreign key or one-to-one
        if isinstance(value, models.Model):
            rel_options = related.get(name, {})
            rel_prefix = rel_options.get('key_prefix', '')
            if rel_prefix and '%(accessor)s' in rel_prefix:
                rel_options['key_prefix'] = rel_prefix % {'accessor': name}

            # Recursve, get the dict representation
            rel_obj_dict = model_to_dict(value, keymap=keymap, camelize=camelize, **rel_options)

            # Check if this object should be merged into the parent object
            if rel_options.get('merge', False):
                for k, v in rel_obj_dict.iteritems():
                    obj_dict[camelize(keymap.get(k, k))] = v
            else:
                obj_dict[camelize(keymap.get(key, key))] = rel_obj_dict

        elif isinstance(value, QuerySet):
            rel_options = related.get(name, {})
            rel_list = queryset_to_list(value, keymap=keymap, camelize=camelize, **rel_options)
            if rel_list:
                obj_dict[camelize(keymap.get(key, key))] = rel_list
        else:
            obj_dict[camelize(keymap.get(key, key))] = value

    return obj_dict


def queryset_to_list(queryset, fields=None, exclude=None, **options):
    if 'select_related' in options:
        queryset = queryset.select_related(*options['select_related'])

    if options.get('values_list', False):
        fields = parse_selectors(queryset.model, fields, exclude)

        # Flatten if only one field is being selected
        if len(fields) == 1:
            flat = options.get('flat', True)
            queryset = queryset.values_list(fields[0], flat=flat)
        else:
            queryset = queryset.values_list(*fields)
        return list(queryset)

    return map(lambda x: model_to_dict(x, fields=fields, exclude=exclude, **options), queryset.iterator())



def serialize(obj, keymap=None, camelize=False, **options):
    """Recursively attempts to find ``Model`` and ``QuerySet`` instances
    to convert them into their representative datastructure per their
    ``Resource`` (if one exists).
    """
    keymap = keymap or {}

    # This will be handled at the iteration
    if camelize is True:
        camelize = convert_to_camel
    elif camelize is False:
        camelize = lambda x: x

    # Handle model instances
    if isinstance(obj, models.Model):
        obj = model_to_dict(obj, keymap=keymap, camelize=camelize,
            **options)

    # Handle querysets
    elif isinstance(obj, QuerySet):
        obj = queryset_to_list(obj, keymap=keymap, camelize=camelize,
            **options)

    # Handle dict instances
    elif isinstance(obj, dict):
        for k, v in obj.iteritems():
            obj[camelize(keymap.get(k, k))] = serialize(v, keymap=keymap,
                camelize=camelize, **options)

    # Handle other iterables
    elif hasattr(obj, '__iter__'):
        obj = map(lambda x: serialize(x, keymap=keymap, camelize=camelize, **options), iter(obj))

    return obj

