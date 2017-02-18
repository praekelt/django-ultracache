import sys

from django.core.cache import cache
from django.contrib.sites.models import Site
try:
    from django.contrib.sites.shortcuts import get_current_site
except ImportError:
    from django.contrib.sites.models import get_current_site
from django.conf import settings


# The metadata itself can"t be allowed to grow endlessly. This value is the
# maximum size in bytes of a metadata list. If your caching backend supports
# compression set a larger value.
try:
    MAX_SIZE = settings.ULTRACACHE["max-registry-value-size"]
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


def cache_meta(request):
    """Inspect request for objects in _ultracache and set appropriate entries
    in Django's cache."""

    #print "CACHE META"
    #print request._ultracache
    #print request._ultracache_cache_key_range
    path = request.get_full_path()

    # List and a dictionary needed for one cache.delete_many and one
    # cache.set_many call.
    all_to_delete = []
    all_to_set = {}

    # In a single-threaded environment templates are rendered recursively
    # depth-first but due to the way we maintain the metadata we don't have to
    # worry about order.
    for start_index, end_index, cache_key in \
        request._ultracache_cache_key_range:

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

        for ctid, obj_pk in request._ultracache[start_index:end_index]:
            # The object appears in these cache entries. If the object is modified
            # then these cache entries are deleted.
            key = "ucache-%s-%s" % (ctid, obj_pk)
            if key not in to_set_get_keys:
                to_set_get_keys.append(key)

            # The object appears in these paths. If the object is modified then any
            # caches that are read from when browsing to this path are cleared.
            key = "ucache-pth-%s-%s" % (ctid, obj_pk)
            if key not in to_set_paths_get_keys:
                to_set_paths_get_keys.append(key)

            # The content type appears in these cache entries. If an object of this
            # content type is created then these cache entries are cleared.
            key = "ucache-ct-%s" % ctid
            if key not in to_set_content_types_get_keys:
                to_set_content_types_get_keys.append(key)

            # The content type appears in these paths. If an object of this content
            # type is created then any caches that are read from when browsing to
            # this path are cleared.
            key = "ucache-ct-pth-%s" % ctid
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

        # Update deletion list
        all_to_delete.extend(to_delete)
        del to_delete

        # Update set dictionary
        for di in (to_set, to_set_paths, to_set_content_types, to_set_content_types_paths):
            for k, v in di.items():
                if k not in all_to_set:
                    all_to_set[k] = []
                all_to_set[k].extend(v)
            del di

        if to_set_objects:
            all_to_set[cache_key + "-objs"] = to_set_objects
            del to_set_objects

    # Remove dupes from lists
    for k, v in all_to_set.items():
        all_to_set[k] = list(set(v))

    #print "ALL TO DELETE"
    #print all_to_delete
    #print "ALL TO SET"
    #print all_to_set

    # Deletion must happen first because set may set some of these keys
    if all_to_delete:
        if "163232e2f0f92da1c20e6c2f2d1b70fc" in all_to_delete:
            print "DELETE"
        try:
            cache.delete_many(all_to_delete)
        except NotImplementedError:
            for k in all_to_delete:
                cache.delete(k)
        del all_to_delete

    # Do one set_many
    if all_to_set:
        if "163232e2f0f92da1c20e6c2f2d1b70fc" in all_to_set:
            print "SET %s" % all_to_set["163232e2f0f92da1c20e6c2f2d1b70fc"]
        try:
            cache.set_many(all_to_set, 86400)
        except NotImplementedError:
            for k, v in all_to_set.items():
                cache.set(k, v, 86400)
        del all_to_set


def get_current_site_pk(request):
    """Seemingly pointless function is so calling code doesn't have to worry
    about the import issues between Django 1.6 and later."""
    return get_current_site(request).pk
