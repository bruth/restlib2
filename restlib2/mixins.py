from django.template import loader
from django.template import RequestContext
from django.http import HttpResponse


class TemplateResponseMixin(object):
    template_name = None
    template_string = None

    def render(self, request, context, *args, **kwargs):
        "Expects the method handler to return the `context` for the template."
        if isinstance(self.template_name, (list, tuple)):
            template = loader.select_template(self.template_name)
        elif self.template_name:
            template = loader.get_template(self.template_name)
        else:
            template = loader.Template(self.template_string)
        context = RequestContext(request, context)
        return HttpResponse(template.render(context))
