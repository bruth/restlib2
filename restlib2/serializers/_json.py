from django.core.serializers.json import simplejson, DjangoJSONEncoder


class JSON(object):
    """Very basic JSON representation encode/decoder. Additional Python types
    are supported via a encoder subclass including: set, Decimal, datetime,
    date and time objects.
    """
    encoder_class = DjangoJSONEncoder
    decoder_class = simplejson.JSONDecoder

    encode_options = {}
    decode_options = {}

    def __init__(self):
        self.encode_options.setdefault('indent', 4)
        self.encode_options.setdefault('sort_keys', True)

    def encode(self, data, options=None, **kwargs):
        if options is None:
            options = self.encode_options

        encoder = self.encoder_class(**options)
        return encoder.encode(data)

    def decode(self, data, options=None, **kwargs):
        if options is None:
            options = self.decode_options

        decoder = self.decoder_class(**options)
        return decoder.decode(data)
