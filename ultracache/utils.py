from django.core.cache import cache


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

        tu = (ctid, obj_pk)
        if tu not in to_set_objects:
            to_set_objects.append(tu)

    # todo: rewrite to handle absence of get_many
    di = cache.get_many(to_set_get_keys)
    for key in to_set_get_keys:
        if key not in to_set:
            to_set[key] = di.get(key, [])
        if cache_key not in to_set[key]:
            to_set[key] = to_set[key] + [cache_key]
    if to_set == di:
        to_set = {}

    di = cache.get_many(to_set_paths_get_keys)
    for key in to_set_paths_get_keys:
        if key not in to_set_paths:
            to_set_paths[key] = di.get(key, [])
        if path not in to_set_paths[key]:
            to_set_paths[key] = to_set_paths[key] + [path]
    if to_set_paths == di:
        to_set_paths = {}

    di = cache.get_many(to_set_content_types_get_keys)
    for key in to_set_content_types_get_keys:
        if key not in to_set_content_types:
            to_set_content_types[key] = di.get(key, [])
        ctid = key.split('-')[-1]
        if ctid not in to_set_content_types[key]:
            to_set_content_types[key] = to_set_content_types[key] + [cache_key]
    if to_set_content_types == di:
        to_set_content_types = {}

    di = cache.get_many(to_set_content_types_paths_get_keys)
    for key in to_set_content_types_paths_get_keys:
        if key not in to_set_content_types_paths:
            to_set_content_types_paths[key] = di.get(key, [])
        if path not in to_set_content_types_paths[key]:
            to_set_content_types_paths[key] = to_set_content_types_paths[key] + [path]
    if to_set_content_types_paths == di:
        to_set_content_types_paths = {}

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

    if to_set_content_types:
        try:
            cache.set_many(to_set_content_types, 86400)
        except NotImplementedError:
            for k, v in to_set_content_types.items():
                cache.set(k, v, 86400)

    if to_set_content_types_paths:
        try:
            cache.set_many(to_set_content_types_paths, 86400)
        except NotImplementedError:
            for k, v in to_set_content_types_paths.items():
                cache.set(k, v, 86400)

    if to_set_objects:
        cache.set(cache_key + '-objs', to_set_objects, 86400)
