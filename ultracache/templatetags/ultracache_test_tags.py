"""Template tag used in unit tests"""

import re

from django import template
from django.core.urlresolvers import reverse, get_script_prefix, resolve
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.conf import settings

register = template.Library()


@register.tag
def render_view(parser, token):
    """{% render_view view_name %}"""
    tokens = token.split_contents()
    if len(tokens) != 2:
        raise template.TemplateSyntaxError(
            "render_view view_name %}"
        )
    return RenderViewNode(tokens[1])


class RenderViewNode(template.Node):

    def __init__(self, view_name):
        self.view_name = template.Variable(view_name)

    def render(self, context):
        view_name = self.view_name.resolve(context)
        url = reverse(view_name)
        # Resolve needs any possible prefix removed
        url = re.sub(r'^%s' % get_script_prefix().rstrip('/'), '', url)
        view, args, kwargs = resolve(url)
        # Call the view. Let any error propagate.
        request = context['request']
        result = view(request, *args, **kwargs)
        if isinstance(result, TemplateResponse):
            # The result of a generic view
            result.render()
            html = result.rendered_content
        elif isinstance(result, HttpResponse):
            # Old-school view
            html = result.content
        return html
