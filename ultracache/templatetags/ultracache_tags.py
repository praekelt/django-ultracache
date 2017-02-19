import hashlib

from django import template
from django.utils.translation import ugettext as _
from django.utils.functional import Promise
from django.templatetags.cache import CacheNode
from django.template.base import VariableDoesNotExist
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.conf import settings

from template_multiprocessing.decorators import multiprocess

from ultracache.utils import cache_meta, get_current_site_pk


register = template.Library()


def callback(request, process_request, last=False):
    if not hasattr(request, "_ultracache"):
        setattr(request, "_ultracache", [])
        setattr(request, "_ultracache_cache_key_range", [])

    print "CALLBACK"
    #print process_request
    #print "CALLBACK 'REQUEST'"
    #print process_request
    #print "xxxxxxxxxxxxxxx"
    #import pdb;pdb.set_trace()

    start_index = len(request._ultracache)
    request._ultracache.extend(process_request["_ultracache"])
    #request._ultracache_cache_key_range.extend(process_request["_ultracache_cache_key_range"])

    for tu in process_request["_ultracache_cache_key_range"]:
        request._ultracache_cache_key_range.append(
            (tu[0] + start_index, tu[1] + start_index, tu[2])
        )

    if last:
        #print "CALLBACK CACHE_META"
        cache_meta(request)


@multiprocess("ultracache.templatetags.ultracache_tags.callback")
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
                "ultracache tag got an unknown variable: %r" % self.expire_time_var.var
            )
        try:
            expire_time = int(expire_time)
        except (ValueError, TypeError):
            raise TemplateSyntaxError(
                "ultracache tag got a non-integer timeout value: %r" % expire_time
            )

        request = context["request"]

        # If request not GET or HEAD never cache
        if request.method.lower() not in ("get", "head"):
            return self.nodelist.render(context)

        # Set a list on the request. Django's template rendering is recursive
        # and single threaded so we can use a list to keep track of contained
        # objects.
        if not hasattr(request, "_ultracache"):
            setattr(request, "_ultracache", [])
            setattr(request, "_ultracache_cache_key_range", [])
            start_index = 0
        else:
            start_index = len(request._ultracache)

        vary_on = []
        if "django.contrib.sites" in settings.INSTALLED_APPS:
            vary_on.append(str(get_current_site_pk(request)))

        for var in self.vary_on:
            try:
                r = var.resolve(context)
            except VariableDoesNotExist:
                pass
            if isinstance(r, Promise):
                r = unicode(r)
            vary_on.append(r)

        # Compute a cache key. In non-debug we want it down to the minimum.
        cache_key = make_template_fragment_key(self.fragment_name, vary_on)
        if not settings.DEBUG:
            cache_key = hashlib.md5(cache_key).hexdigest()

        value = cache.get(cache_key)
        if value is None:
            print "CACHE MISS FOR %s" % cache_key

            # The outermost tag is responsible for calling cache_meta. Mark it
            # if not marked yet.
            outer = False
            if not hasattr(request, "_ultracache_outer_node"):
                setattr(request, "_ultracache_outer_node", True)
                outer = True

            value = self.nodelist.render(context)

            # Keep track of which variables belong to this tag
            #print "NORMAL ADD CACHE_KEY_RANGE"
            #print (start_index, len(request._ultracache), cache_key)
            request._ultracache_cache_key_range.append(
                (start_index, len(request._ultracache), cache_key)
            )

            if cache_key == "163232e2f0f92da1c20e6c2f2d1b70fc":
                print "SET %s" % value
            cache.set(cache_key, value, expire_time)

            # Finally call cache meta if we are the outer tag
            if outer and not hasattr(self.__class__, "__multiprocess_safe__"):
                cache_meta(request)

        else:
            print "CACHE HIT FOR %s" % cache_key

            # A cached result was found. Set tuples in _ultracache manually so
            # outer template tags are aware of contained objects.
            for tu in cache.get(cache_key + "-objs", []):
                #print "IN CACHE MISS ADD %s" % str(tu)
                request._ultracache.append(tu)

        return value


@register.tag("ultracache")
def do_ultracache(parser, token):
    """Based on Django's default cache template tag"""
    nodelist = parser.parse(("endultracache",))
    parser.delete_first_token()
    tokens = token.split_contents()
    if len(tokens) < 3:
        raise TemplateSyntaxError(""%r" tag requires at least 2 arguments." % tokens[0])
    return UltraCacheNode(nodelist,
        parser.compile_filter(tokens[1]),
        tokens[2], # fragment_name can"t be a variable.
        [parser.compile_filter(token) for token in tokens[3:]])
