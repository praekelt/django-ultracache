import md5
import types
from functools import wraps

from django.http import HttpResponse
from django.core.cache import cache
from django.utils.decorators import available_attrs
from django.views.generic.base import TemplateResponseMixin
from django.conf import settings

from ultracache.utils import cache_meta


def cached_get(timeout, *params):

    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(view_or_request, *args, **kwargs):

            # The type of the request gets muddled when using a function based
            # decorator. We must use a function based decorator so it can be
            # used in urls.py.
            request = getattr(view_or_request, 'request', view_or_request)

            # If request not GET or HEAD never cache
            if request.method.lower() not in ('get', 'head'):
                return view_func(view_or_request, *args, **kwargs)

            # If request contains messages never cache
            l = 0
            try:
                l = len(request._messages)
            except (AttributeError, TypeError):
                pass
            if l:
                return view_func(view_or_request, *args, **kwargs)

            # Compute a cache key
            li = [str(view_or_request.__class__), view_func.__name__]

            # request.get_full_path is implicitly added it no other request
            # path is provided. get_full_path includes the querystring and is
            # the more conservative approach but makes it trivially easy for a
            # request to bust through the cache.
            if not set(params).intersection(set((
                "request.get_full_path()", "request.path", "request.path_info"
            ))):
                li.append(request.get_full_path())

            if 'django.contrib.sites' in settings.INSTALLED_APPS:
                li.append(settings.SITE_ID)

            # Pre-sort kwargs
            keys = kwargs.keys()
            keys.sort()
            for key in keys:
                li.append('%s,%s' % (key, kwargs[key]))

            # Extend cache key with custom variables
            for param in params:
                if not isinstance(param, types.StringType):
                    param = str(param)
                li.append(eval(param))

            hashed = md5.new(':'.join([str(l) for l in li])).hexdigest()
            cache_key = 'ucache-get-%s' % hashed
            cached = cache.get(cache_key, None)
            if cached is None:
                # The get view as outermost caller may bluntly set _ultracache
                request._ultracache = []
                response = view_func(view_or_request, *args, **kwargs)
                content = getattr(response, 'rendered_content', None) \
                    or getattr(response, 'content', None)
                if content is not None:
                    headers = getattr(response, '_headers', {})
                    cache.set(
                        cache_key,
                        {'content': content, 'headers': headers},
                        timeout
                    )
                    cache_meta(request, cache_key)
            else:
                response = HttpResponse(cached['content'])
                # Headers has a non-obvious format
                for k, v in cached['headers'].items():
                    response[v[0]] = v[1]

            return response

        return _wrapped_view
    return decorator
