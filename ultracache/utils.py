from django.core.cache import cache


def cache_meta(request, cache_key, start_index=0):
    """Inspect request for objects in _ultracache and set appropriate entries
    in Django's cache.  """

    path = request.get_full_path()
    to_set = {}
    to_set_paths = {}
    to_set_content_types = {}
    to_set_content_types_paths = {}
    to_set_objects = []
    for ctid, obj_pk in request._ultracache[start_index:]:
        key = 'ucache-%s-%s' % (ctid, obj_pk)
        to_set.setdefault(key, cache.get(key, []))
        if cache_key not in to_set[key]:
            to_set[key].append(cache_key)

        key = 'ucache-pth-%s-%s' % (ctid, obj_pk)
        to_set_paths.setdefault(key, cache.get(key, []))
        if path not in to_set_paths[key]:
            to_set_paths[key].append(path)

        key = 'ucache-ct-%s' % ctid
        to_set_content_types.setdefault(key, cache.get(key, []))
        if ctid not in to_set_content_types[key]:
            to_set_content_types[key].append(cache_key)

        key = 'ucache-ct-pth-%s' % ctid
        to_set_content_types_paths.setdefault(key, cache.get(key, []))
        if path not in to_set_content_types_paths[key]:
            to_set_content_types_paths[key].append(path)

        tu = (ctid, obj_pk)
        if tu not in to_set_objects:
            to_set_objects.append(tu)

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
