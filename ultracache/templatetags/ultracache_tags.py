from django import template
from django.utils.translation import ugettext as _
from django.utils.functional import Promise
from django.templatetags.cache import CacheNode
from django.template import resolve_variable
from django.template.base import VariableDoesNotExist
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.conf import settings

from ultracache import tracker
from ultracache.utils import cache_meta


register = template.Library()


class UltraCacheNode(CacheNode):
    """Based on Django's default cache template tag. Add SITE_ID as implicit
    vary on parameter is sites product is installed. Allow unresolvable
    variables. Allow translated strings."""

    def __init__(self, *args):
        # Django 1.7 introduced cache_name. Using different caches makes
        # invalidation difficult. It will be supported in a future version.
        try:
            super(UltraCacheNode, self).__init__(*args, cache_name=None)
        except TypeError:
            super(UltraCacheNode, self).__init__(*args)

    def render(self, context):
        try:
            expire_time = self.expire_time_var.resolve(context)
        except VariableDoesNotExist:
            raise TemplateSyntaxError(
                '"cache" tag got an unknown variable: %r' % self.expire_time_var.var
            )
        try:
            expire_time = int(expire_time)
        except (ValueError, TypeError):
            raise TemplateSyntaxError(
                '"cache" tag got a non-integer timeout value: %r' % expire_time
            )

        # Set a list on the context
        request = context.get('request', None)
        if not '_ultracache_key' in context:
            tracker_key = tracker.get_new_key()
            context['_ultracache_key'] = tracker_key
            start_index = 0
        else:
            start_index = len(tracker[context['_ultracache_key']])

        vary_on = []
        if 'django.contrib.sites' in settings.INSTALLED_APPS:
            vary_on.append(str(settings.SITE_ID))

        for var in self.vary_on:
            try:
                r = var.resolve(context)
            except VariableDoesNotExist:
                pass
            if isinstance(r, Promise):
                r = unicode(r)
            vary_on.append(r)

        cache_key = make_template_fragment_key(self.fragment_name, vary_on)
        value = cache.get(cache_key)
        if value is None:
            value = self.nodelist.render(context)
            cache.set(cache_key, value, expire_time)
            cache_meta(request, tracker[context['_ultracache_key']], cache_key, start_index)
        else:
            # A cached result was found. Set tuples in _ultracache manually so
            # outer template tags are aware of contained objects.
            for tu in cache.get(cache_key + '-objs', []):
                tracker[context['_ultracache_key']].append(tu)

        return value


@register.tag('ultracache')
def do_ultracache(parser, token):
    """Based on Django's default cache template tag"""
    nodelist = parser.parse(('endultracache',))
    parser.delete_first_token()
    tokens = token.split_contents()
    if len(tokens) < 3:
        raise TemplateSyntaxError("'%r' tag requires at least 2 arguments." % tokens[0])
    return UltraCacheNode(nodelist,
        parser.compile_filter(tokens[1]),
        tokens[2], # fragment_name can't be a variable.
        [parser.compile_filter(token) for token in tokens[3:]])
