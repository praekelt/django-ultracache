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

You can create custom reverse caching proxy purgers. See ``purgers.py`` for examples::

    ULTRACACHE = {
        'purge': {'method': 'myproduct.purgers.squid'}
    }

Automatic invalidation defaults to true. To disable automatic invalidation set::

    ULTRACACHE = {
        'invalidate': False
    }

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

