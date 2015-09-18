Changelog
=========

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

