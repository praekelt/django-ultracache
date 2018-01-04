from collections import OrderedDict


class DummyProxy(dict):

    def make_key(self, path, headers=None):
        key = path
        if headers is not None:
            key += str(frozenset(sorted(headers.items())))
        return key

    def cache(self, request, value):
        headers = {k[5:].replace("_", "-").lower(): v for \
            k, v in request.META.items() if k.startswith("HTTP_")}
        key = self.make_key(request.get_full_path(), headers)
        self[key] = value

    def is_cached(self, path, headers=None):
        # The test framework sends an empty cookie with each request. Avoid
        # copy pasta in the individual tests and just add that header here.
        if headers is None:
            headers = {u"cookie": u""}
        key = self.make_key(path, headers)
        return key in self

    def purge(self, path, headers=None):
        key = self.make_key(path, headers)
        if key in self:
            del self[key]

dummy_proxy = DummyProxy()


def dummy_purger(path, headers=None):
    dummy_proxy.purge(path, headers=headers)
