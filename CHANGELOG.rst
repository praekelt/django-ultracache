Changelog
=========

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

