class DummyProxy(dict):

    def cache(self, path, value):
        self[path] = value

    def is_cached(self, path):
        return path in self

    def purge(self, path):
        if path in self:
            del self[path]

dummy_proxy = DummyProxy()


def dummy_purger(path):
    dummy_proxy.purge(path)
