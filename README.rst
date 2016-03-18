Django Ultracache
=================
**Drop-in replacement for Django's template fragment caching. Provides automatic Django cache invalidation and reverse caching proxy purging.**

.. figure:: https://travis-ci.org/praekelt/django-ultracache.svg?branch=develop
   :align: center
   :alt: Travis

.. contents:: Contents
    :depth: 5

Installation
------------

#. Install or add ``django-ultracache`` to your Python path.

#. Add ``ultracache`` to your ``INSTALLED_APPS`` setting.

#. Ensure ``django.core.context_processors.request`` is in ``TEMPLATE_CONTEXT_PROCESSORS`` setting.

Usage
-----

``django-ultracache`` provides a template tag ``{% ultracache %}`` that functions like Django's
standard cache template tag, with these exceptions.

#. It takes the sites framework into consideration, allowing different caching per site.

#. It allows undefined variables to be passed as arguments, thus simplifying the template.

#. Crucially, it is aware of model objects that are subjected to its caching. When an object is modified
   all affected cache key are automatically expired. This allows the user to set longer expiry times without having
   to worry about stale content.

#. The cache invalidation can be extended to issue purge commands to Varnish, Nginx or other reverse caching proxies.

Simplest use case::

    {% load ultracache_tags %}
    {% ultracache 3600 'my_identifier' object 123 undefined 'string' %}
        {{ object.title }}
    {% endultracache %}

The tag can be nested. ``ultracache`` is aware of all model objects that are subjected to its caching.
In this example cache keys ``outer`` and ``inner_one`` are expired when object one is changed but
cache key ``inner_two`` remains unaffected::

    {% load ultracache_tags %}
    {% ultracache 1200 'outer' %}
        {% ultracache 1200 'inner_one' %}
            title = {{ one.title }}
        {% endultracache %}
        {% ultracache 1200 'inner_two' %}
            title = {{ two.title }}
        {% endultracache %}
    {% endultracache %}

``django-ultracache`` also provides a decorator ``cached_get`` to cache your views. The parameters
follow the same rules as the ``ultracache`` template tag except they must all resolve. ``request.get_full_path()`` is
always implicitly added to the cache key::

    from ultracache.decorators import cached_get


    class CachedView(TemplateView):
        template_name = "ultracache/cached_view.html"

        @cached_get(300, "request.is_secure()", 456)
        def get(self, *args, **kwargs):
            return super(CachedView, self).get(*args, **kwargs)

The ``cached_get`` decorator can be used in an URL pattern::

    from ultracache.decorators import cached_get

    url(
        r"^cached-view/$",
        cached_get(3600)(TemplateView.as_view(
            template_name="myproduct/template.html"
        )),
        name="cached-view"
    )

Do not indiscriminately use the ``cached_get`` decorator. It only ever operates on GET requests
but cannot know if the code being wrapped retrieves data from eg. the session. In such a case
it will cache things it is not supposed to cache.

If your view is used by more than one URL pattern then it is highly recommended to
apply the ``cached_get`` decorator in the URL pattern. Applying it at class level
may lead to cache collisions, especially if ``get_template_names`` is overridden.

You can create custom reverse caching proxy purgers. See ``purgers.py`` for examples::

    ULTRACACHE = {
        'purge': {'method': 'myproduct.purgers.squid'}
    }

Automatic invalidation defaults to true. To disable automatic invalidation set::

    ULTRACACHE = {
        'invalidate': False
    }

``django-ultracache`` maintains a registry in Django's caching backend (see `How does it work`). This registry
can't be allowed to grow unchecked, thus a limit is imposed on the registry size. It would be inefficient to
impose a size limit on the entire registry so a maximum size is set per cached value. It defaults to 25000 bytes::

    ULTRACACHE = {
        'max-registry-value-size': 10000
    }

It is highly recommended to use a backend that supports compression because a larger size improves cache coherency.


How does it work?
-----------------

``django-ultracache`` monkey patches ``django.template.base.Variable._resolve_lookup`` to make a record of
model objects as they are resolved. The ``ultracache`` template tag inspects the list of objects contained
within it and keeps a registry in Django's caching backend. A ``post_save`` signal handler monitors objects
for changes and expires the appropriate cache keys.

Tips
----

#. If you arre running a cluster of Django nodes then ensure that they use a shared caching backend.

#. Expose objects in your templates. Instead of passing ``object_title`` to a template rather have the
   template dereference ``object.title``.

