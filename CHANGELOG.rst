Changelog
=========

1.9.0
-----
#. Move to tox for tests.
#. Django 1.9 compatibility.

0.3.8
-----
#. Honor the `raw` parameter send along by loaddata. It prevents redundant post_save handling.

0.3.7
-----
#. Revert the adding of the template name. It introduces a performance penalty in a WSGI environment.
#. Further reduce the number of writes to the cache.

0.3.6
-----
#. Add template name (if possible) to the caching key.
#. Reduce number of calls to set_many.

0.3.5
-----
#. Keep the metadata cache size in check to prevent possibly infinite growth.

0.3.4
-----
#. Prevent redundant sets.
#. Work around an apparent Python bug related to `di[k].append(v)` vs `di[k] = di[k] + [v]`. The latter is safe.

0.3.3
-----
#. Handle case where one cached view renders another cached view inside it, thus potentially sharing the same cache key.

0.3.2
-----
#. The `ultracache` template tag now only caches HEAD and GET requests.

0.3.1
-----
#. Trivial release to work around Pypi errors of the day.

0.3
---
#. Replace `cache.get` in for loop with `cache.get_many`.

0.2
---
#. Do not automatically add `request.get_full_path()` if any of `request.get_full_path()`, `request.path` or `request.path_info` is an argument for `cached_get`.

0.1.6
-----
#. Also cache response headers.

0.1.5
-----
#. Explicitly check for GET and HEAD request method and cache only those requests.

0.1.4
-----
#. Rewrite decorator to be function based instead of class based so it is easier to use in urls.py.

0.1.3
-----
#. `cached_get` decorator now does not cache if request contains messages.

0.1.2
-----
#. Fix HTTPResponse caching bug.

0.1.1
-----
#. Handle case where a view returns an HTTPResponse object.

0.1
---
#. Initial release.

