import warnings
from . import _json, _plain, _octet, _xml, _www

class Library(object):
    library = {}

    def __contains__(self, key):
        return key in self.library

    @classmethod
    def register(cls, mimetype, klass):
        if mimetype in cls.library:
            warnings.warn('Re-registering for %s' % mimetype)

        cls.library[mimetype] = klass()

    @classmethod
    def unregister(cls, mimetype):
        cls.library.pop(mimetype, None)

    def encode(self, mimetype, data, **kwargs):
        if mimetype not in self.library:
            raise KeyError('Encoder for %s not registered' % mimetype)
        if isinstance(data, basestring):
            raise TypeError('Content is already a string, cannot encode.')
        return self.library[mimetype].encode(data, **kwargs)

    def decode(self, mimetype, data, **kwargs):
        if mimetype not in self.library:
            raise KeyError('Decoder for %s not registered' % mimetype)
        if not isinstance(data, basestring):
            raise TypeError('Content is not a string, cannot decode.')
        return self.library[mimetype].decode(data, **kwargs)

    def supports_encoding(self, mimetype):
        if mimetype not in self:
            return None
        return hasattr(self.library[mimetype], 'encode')

    def supports_decoding(self, mimetype):
        if mimetype not in self:
            return None
        return hasattr(self.library[mimetype], 'decode')

serializers = Library()

# register built-in encoders/decoders
serializers.register('application/x-www-form-urlencoded', _www.UrlEncoded)
serializers.register('application/octet-stream', _octet.OctetStream)
serializers.register('text/plain', _plain.PlainText)
serializers.register('application/json', _json.JSON)
serializers.register('application/xml', _xml.DataOrientedXML)
