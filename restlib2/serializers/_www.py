from django.http import QueryDict

class UrlEncoded(object):
    def decode(self, data, **kwargs):
        return QueryDict(data)
