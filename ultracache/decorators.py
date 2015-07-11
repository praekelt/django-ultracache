import md5

from django.http import HttpResponse
from django.core.cache import cache
from django.conf import settings


def cached_get(**kwargs):
    """Decorator that caches rendered result for DetailView and ListView
    subclasses.
    """
    def real_cached_get(func):
        def new(self, request, *args, **kwargs):
            # Compute a cache key, taking care to pre-sort kwargs
            #context!!!
            li = [request.get_full_path()]
            if 'django.contrib.sites' in settings.INSTALLED_APPS:
                li.append(settings.SITE_ID)
            keys = kwargs.keys()
            keys.sort()
            for key in keys:
                li.append('%s,%s' % (key, kwargs[key]))
            hashed = md5.new(':'.join([str(l) for l in li])).hexdigest()
            key = 'ucache-get-%s' % hashed
            cached = cache.get(key, None)
            if cached is not None:
                return HttpResponse(cached)
            response = func(self, request, *args, **kwargs)
            # This decorator isn't supposed to be applied to gets that may
            # redirect, so don't try to catch those errors.
            cache.set(key, response.rendered_content, 300)
            return response
        return new
    return real_cached_get
