import hashlib

from django.core.cache import cache


class EmptyMarker:
    pass
empty_marker = EmptyMarker()


class Ultracache:

    def __init__(self, timeout, params):
        self.timeout = timeout
        self.params = params
        self.result = empty_marker

    def __enter__(self):
        s = ":".join([str(p) for p in self.params])
        hashed = hashlib.md5(s.encode("utf-8")).hexdigest()
        self.cache_key = "ucache-get-%s" % hashed
        cached = cache.get(self.cache_key, empty_marker)
        if cached is not empty_marker:
            return cached
        return self.result

    def __exit__(self, *args):
        if self.result is not empty_marker:
            cache.set(self.cache_key, self.result, self.timeout)


