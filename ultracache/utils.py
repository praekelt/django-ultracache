import sys

from django.core.cache import cache
from django.conf import settings


# The metadata itself can't be allowed to grow endlessly. This value is the
# maximum size in bytes of a metadata list. If your caching backend supports
# compression set a larger value.
try:
    MAX_SIZE = settings.ULTRACACHE['max-registry-value-size']
except (AttributeError, KeyError):
    MAX_SIZE = 25000


def reduce_list_size(li):
    """Return two lists
        - the last N items of li whose total size is less than MAX_SIZE
        - the rest of the original list li
    """
    size = sys.getsizeof(li)
    keep = li
    toss = []
    n = len(li)
    decrement_by = max(n / 10, 10)
    while (size >= MAX_SIZE) and (n > 0):
        n -= decrement_by
        toss = li[:-n]
        keep = li[-n:]
        size = sys.getsizeof(keep)
    return keep, toss


def cache_meta(request, cache_key, start_index=0):
    """Inspect request for objects in _ultracache and set appropriate entries
    in Django's cache."""

    path = request.get_full_path()

    # Lists needed for cache.get_many
    to_set_get_keys = []
    to_set_paths_get_keys = []
    to_set_content_types_get_keys = []
    to_set_content_types_paths_get_keys = []

    # Dictionaries needed for cache.set_many
    to_set = {}
    to_set_paths = {}
    to_set_content_types = {}
    to_set_content_types_paths = {}

    to_delete = []
    to_set_objects = []

    for ctid, obj_pk in request._ultracache[start_index:]:
        # The object appears in these cache entries. If the object is modified
        # then these cache entries are deleted.
        key = 'ucache-%s-%s' % (ctid, obj_pk)
        if key not in to_set_get_keys:
            to_set_get_keys.append(key)

        # The object appears in these paths. If the object is modified then any
        # caches that are read from when browsing to this path are cleared.
        key = 'ucache-pth-%s-%s' % (ctid, obj_pk)
        if key not in to_set_paths_get_keys:
            to_set_paths_get_keys.append(key)

        # The content type appears in these cache entries. If an object of this
        # content type is created then these cache entries are cleared.
        key = 'ucache-ct-%s' % ctid
        if key not in to_set_content_types_get_keys:
            to_set_content_types_get_keys.append(key)

        # The content type appears in these paths. If an object of this content
        # type is created then any caches that are read from when browsing to
        # this path are cleared.
        key = 'ucache-ct-pth-%s' % ctid
        if key not in to_set_content_types_paths_get_keys:
            to_set_content_types_paths_get_keys.append(key)

        # A list of objects that contribute to a cache entry
        tu = (ctid, obj_pk)
        if tu not in to_set_objects:
            to_set_objects.append(tu)

    # todo: rewrite to handle absence of get_many
    di = cache.get_many(to_set_get_keys)
    for key in to_set_get_keys:
        v = di.get(key, None)
        keep = []
        if v is not None:
            keep, toss = reduce_list_size(v)
            if toss:
                to_set[key] = keep
                to_delete.extend(toss)
        if cache_key not in keep:
            if key not in to_set:
                to_set[key] = keep
            to_set[key] = to_set[key] + [cache_key]
    if to_set == di:
        to_set = {}

    di = cache.get_many(to_set_paths_get_keys)
    for key in to_set_paths_get_keys:
        v = di.get(key, None)
        keep = []
        if v is not None:
            keep, toss = reduce_list_size(v)
            if toss:
                to_set_paths[key] = keep
        if path not in keep:
            if key not in to_set_paths:
                to_set_paths[key] = keep
            to_set_paths[key] = to_set_paths[key] + [path]
    if to_set_paths == di:
        to_set_paths = {}

    di = cache.get_many(to_set_content_types_get_keys)
    for key in to_set_content_types_get_keys:
        v = di.get(key, None)
        keep = []
        if v is not None:
            keep, toss = reduce_list_size(v)
            if toss:
                to_set_content_types[key] = keep
                to_delete.extend(toss)
        if cache_key not in keep:
            if key not in to_set_content_types:
                to_set_content_types[key] = keep
            to_set_content_types[key] = to_set_content_types[key] + [cache_key]
    if to_set_content_types == di:
        to_set_content_types = {}

    di = cache.get_many(to_set_content_types_paths_get_keys)
    for key in to_set_content_types_paths_get_keys:
        v = di.get(key, None)
        keep = []
        if v is not None:
            keep, toss = reduce_list_size(v)
            if toss:
                to_set_content_types_paths[key] = keep
        if path not in keep:
            if key not in to_set_content_types_paths:
                to_set_content_types_paths[key] = keep
            to_set_content_types_paths[key] = to_set_content_types_paths[key] + [path]
    if to_set_content_types_paths == di:
        to_set_content_types_paths = {}

    # Deletion must happen first because set may set some of these keys
    if to_delete:
        try:
            cache.delete_many(to_delete)
        except NotImplementedError:
            for k in to_delete:
                cache.delete(k)

    # Do one set_many
    di = {}
    di.update(to_set)
    del to_set
    di.update(to_set_paths)
    del to_set_paths
    di.update(to_set_content_types)
    del to_set_content_types
    di.update(to_set_content_types_paths)
    del to_set_content_types_paths

    if to_set_objects:
        di[cache_key + '-objs'] = to_set_objects

    if di:
        try:
            cache.set_many(di, 86400)
        except NotImplementedError:
            for k, v in di.items():
                cache.set(k, v, 86400)
