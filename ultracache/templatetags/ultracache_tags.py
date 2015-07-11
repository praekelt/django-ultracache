from django import template
from django.utils.translation import ugettext as _
from django.utils.functional import Promise
from django.templatetags.cache import CacheNode
from django.template import resolve_variable
from django.template.base import VariableDoesNotExist
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.conf import settings

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

        # Set a list on the request. Context may be pushed and popped and is
        # not reliable.
        if not hasattr(context, '_ultracache'):
            setattr(context, '_ultracache', [])
            start_index = 0
        else:
            start_index = len(context._ultracache)

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

        # Cache the ultracache cache keys and paths each object appears in
        to_set = {}
        to_set_paths = {}
        for ctid, obj_pk, path in context._ultracache[start_index:]:
            key = 'ucache-%s-%s' % (ctid, obj_pk)
            to_set.setdefault(key, cache.get(key, []))
            if cache_key not in to_set[key]:
                to_set[key].append(cache_key)
            key = 'ucache-pth-%s-%s' % (ctid, obj_pk)
            to_set_paths.setdefault(key, [])
            if path not in to_set_paths[key]:
                to_set_paths[key].append(path)
        if to_set:
            try:
                cache.set_many(to_set, 86400)
            except NotImplementedError:
                for k, v in to_set.items():
                    cache.set(k, v, 86400)
        if to_set_paths:
            try:
                cache.set_many(to_set_paths, 86400)
            except NotImplementedError:
                for k, v in to_set_paths.items():
                    cache.set(k, v, 86400)

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
