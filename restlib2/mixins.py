from django.template import loader
from django.template import RequestContext
from django.http import HttpResponse
from .http import codes


class TemplateResponseMixin(object):
    template_name = None
    template_string = None

    def render(self, request, context, status=codes.ok, content_type=None,
            args=None, kwargs=None):
        "Expects the method handler to return the `context` for the template."

        if isinstance(self.template_name, (list, tuple)):
            template = loader.select_template(self.template_name)
        elif self.template_name:
            template = loader.get_template(self.template_name)
        else:
            template = loader.Template(self.template_string)

        context = RequestContext(request, context)
        content = template.render(context)

        return HttpResponse(content, status=status, content_type=content_type)
