import md5
import types

from django.http import HttpResponse
from django.core.cache import cache
from django.conf import settings


class cached_get(object):

    def __init__(self, timeout, *args):
        self.timeout=  timeout
        self.args = args

    def __call__(self, f):

        def wrapped_f(cls, request, *args, **kwargs):

            # Compute a cache key
            li = [request.get_full_path()]
            if 'django.contrib.sites' in settings.INSTALLED_APPS:
                li.append(settings.SITE_ID)

            # Pre-sort kwargs
            keys = kwargs.keys()
            keys.sort()
            for key in keys:
                li.append('%s,%s' % (key, kwargs[key]))

            # Extend cache key with custom variables
            for arg in self.args:
                if not isinstance(arg, types.StringType):
                    arg = str(arg)
                li.append(eval(arg))

            hashed = md5.new(':'.join([str(l) for l in li])).hexdigest()
            key = 'ucache-get-%s' % hashed
            cached = cache.get(key, None)
            if cached is not None:
                return HttpResponse(cached)
            response = f(cls, request, *args, **kwargs)
            # This decorator isn't supposed to be applied to gets that may
            # redirect, so don't try to catch those errors.
            cache.set(key, response.rendered_content, self.timeout)
            return response

        return wrapped_f
