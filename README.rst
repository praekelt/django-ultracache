PLEASE NOTE!!

This repo has moved to this fork: https://github.com/hedleyroos/django-ultracache and will be maintained there.




Django Ultracache
=================
**Cache views, template fragments and arbitrary Python code. Monitor Django object changes to perform automatic fine-grained cache invalidation from Django level, through proxies, to the browser.**

.. figure:: https://travis-ci.org/praekelt/django-ultracache.svg?branch=develop
   :align: center
   :alt: Travis

.. contents:: Contents
    :depth: 5

Overview
--------

Cache views, template fragments and arbitrary Python code. Once cached we
either avoid database queries and expensive computations, depending on the use
case. In all cases affected caches are automatically expired when objects "red"
or "blue" are modified, without us having to add "red" or "blue" to the cache.

View::

    from ultracache.decorators import cached_get, ultracache

    @ultracache(300)
    class MyView(TemplateView):
        template_name = "my_view.html"

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            # Note we never use red
            red = Color.objects.get(slug="red")
            # For our example color_slug is blue
            context["color"] = Color.objects.get(slug=kwargs["color_slug"])
            return context

Template::

    {# variable "color" is the object "blue" #}
    {% load ultracache_tags %}
    {% ultracache 300 "color-info" color.pk %}
        {# expensive properties #}
        {{ color.compute_valid_hex_codes }}
        {{ color.name_in_all_languages }}
    {% endultracache %}

Python::

    from ultracache.utils import Ultracache

    ...

    color_slug = request.GET["color_slug"]
    uc = Ultracache(300, "another-identifier", color_slug)
    if uc:
        codes = uc.cached
    else:
        color = Color.objects.get(slug=color_slug)
        codes = color.compute_valid_hex_codes()
        uc.cache(codes)
    print(codes)

Installation
------------

#. Install or add ``django-ultracache`` to your Python path.

#. Add ``ultracache`` to your ``INSTALLED_APPS`` setting.

#. Ensure ``django.template.context_processors.request`` is in the context processors setting.

Features
--------

#. Caches template fragments, views, Django Rest Framework viewsets.

#. It takes the sites framework into consideration, allowing different caching per site.

#. Crucially, it is aware of model objects that are subjected to its caching. When an object is modified
   all affected cache key are automatically expired. This allows the user to set longer expiry times without having
   to worry about stale content.

#. The cache invalidation can be extended to issue purge commands to Varnish, Nginx or other reverse caching proxies.

Usage
-----

The ``cached_get`` and ``ultracache`` view decorators
*****************************************************

``django-ultracache`` also provides decorators ``cached_get`` and
``ultracache`` to cache your views. The parameters follow the same rules as the
``ultracache`` template tag except they must all resolve.
``request.get_full_path()`` is always implicitly added to the cache key. The
``ultracache`` decorator is newer and cleaner, so use that where possible::

    from ultracache.decorators import cached_get, ultracache


    class CachedView(TemplateView):
        template_name = "cached_view.html"

        @cached_get(300, "request.is_secure()", 456)
        def get(self, *args, **kwargs):
            return super(CachedView, self).get(*args, **kwargs)

    @ultracache(300, "request.is_secure()", 456)
    class AnotherCachedView(TemplateView):
        template_name = "cached_view.html"

The ``cached_get`` decorator can be used in an URL pattern::

    from ultracache.decorators import cached_get

    url(
        r"^cached-view/$",
        cached_get(3600)(TemplateView.as_view(
            template_name="myproduct/template.html"
        )),
        name="cached-view"
    )

Do not indiscriminately use the decorators. They only ever operate on GET
requests but cannot know if the code being wrapped retrieves data from eg. the
session. In such a case they will cache things they are not supposed to cache.

If your view is used by more than one URL pattern then it is highly recommended
to apply the ``cached_get`` decorator in the URL pattern. Applying it directly
to the ``get`` method may lead to cache collisions, especially if
``get_template_names`` is overridden.

The ``ultracache`` template tag
*******************************

``django-ultracache`` provides a template tag ``{% ultracache %}`` that
functions much like Django's standard cache template tag; however, it takes the
sites framework into consideration, allowing different caching per site, and it
handles undefined variables.

Simplest use case::

    {% load ultracache_tags %}
    {% ultracache 3600 "my_identifier" object 123 undefined "string" %}
        {{ object.title }}
    {% endultracache %}

The tag can be nested. ``ultracache`` is aware of all model objects that are subjected to its caching.
In this example cache keys ``outer`` and ``inner_one`` are expired when object one is changed but
cache key ``inner_two`` remains unaffected::

    {% load ultracache_tags %}
    {% ultracache 1200 "outer" %}
        {% ultracache 1200 "inner_one" %}
            title = {{ one.title }}
        {% endultracache %}
        {% ultracache 1200 "inner_two" %}
            title = {{ two.title }}
        {% endultracache %}
    {% endultracache %}

Specifying a good cache key
***************************

The cache key decides whether a piece of code or template is going to be evaluated further. The
cache key must therefore accurately and minimally describe what is being subjected to caching.

todo

Django Rest Framework viewset caching
*************************************

Cache ``list`` and ``retrieve`` actions on viewsets::

    # Cache all viewsets
    ULTRACACHE = {
        "drf": {"viewsets": {"*": {}}}

    }

    # Cache a specific viewset by name
    ULTRACACHE = {
        "drf": {"viewsets": {"my.app.MyViewset": {}}}

    }

    # Cache a specific viewset by class
    ULTRACACHE = {
        "drf": {"viewsets": {MyViewset: {}}}

    }

    # Timeouts default to 300 seconds
    ULTRACACHE = {
        "drf": {"viewsets": {"*": {"timeout": 1200}}}

    }

    # Evaluate code to append to the cache key. This example caches differently
    # depending on whether the user is logged in or not.
    ULTRACACHE = {
        "drf": {"viewsets": {"*": {"evaluate": "request.user.is_anonymous"}}}

    }

    # Evaluate code to append to the cache key via a callable.
    def mycallable(viewset, request):
        if viewset.__class__.__name__ == "foo":
            return request.user.id

    ULTRACACHE = {
        "drf": {"viewsets": {"*": {"evaluate": mycallable}}}

    }

Purgers
*******

You can create custom reverse caching proxy purgers. See ``purgers.py`` for examples::

    ULTRACACHE = {
        "purge": {"method": "myproduct.purgers.squid"}
    }

The most useful purger is ``broadcast``. As the name implies it broadcasts purge
instructions to a queue. Note that you need celery running and configured to
write to a RabbitMQ instance for this to work correctly.

The purge instructions are consumed by the ``cache-purge-consumer.py`` script.
The script reads a purge instruction from the queue and then sends a purge
instruction to an associated reverse caching proxy. To run the script::

    virtualenv ve
    ./ve/bin/pip install -e .
    ./ve/bin/python bin/cache-purge-consumer.py -c config.yaml

The config file has these options:

#. rabbit-url
   Specify RabbitMQ connection parameters in the AMQP URL format
   ``amqp://username:password@host:port/<virtual_host>[?query-string]``.
   *Optional. Defaults to ``amqp://guest:guest@127.0.0.1:5672/%2F``. Note the
   URL encoding for the path.*

#. host
   A reverse caching proxy may be responsible for many domains (hosts), and
   ultracache will keep track of the host that is involved in a purge request;
   however, if you have a use case that does not supply a hostname, eg. doing a
   PURGE request via curl, then forcing a hostname solves the use case.
   *Optional.*

#. proxy-address
   The IP address or hostname of the reverse caching proxy.
   *Optional. Defaults to 127.0.0.1.*

#. logfile
   Set to a file to log all purge instructions. Specify ``stdout`` to log to
   standard out.
   *Optional.*

Other settings
**************

Automatic invalidation defaults to true. To disable automatic invalidation set::

    ULTRACACHE = {
        "invalidate": False
    }

``django-ultracache`` maintains a registry in Django's caching backend (see
`How does it work`). This registry can"t be allowed to grow unchecked, thus a
limit is imposed on the registry size. It would be inefficient to impose a size
limit on the entire registry so a maximum size is set per cached value. It
defaults to 1000000 bytes::

    ULTRACACHE = {
        "max-registry-value-size": 10000
    }

It is highly recommended to use a backend that supports compression because a
larger size improves cache coherency.

If you make use of a reverse caching proxy then you need the original set of
request headers (or a relevant subset) to purge paths from the proxy correctly.
The problem with the modern web is the sheer amount of request headers present
on every request would lead to a large number of entries having to be stored by
``django-ultracache`` in Django's caching backend. Your proxy probably has a
custom hash computation rule that considers only the request path (always
implied) and Django's sessionid cookie, so define a setting to also consider only
the cookie on the Django side::

    ULTRACACHE = {
        "consider-headers": ["cookie"]
    }

If you only need to consider some cookies then set::

    ULTRACACHE = {
        "consider-cookies": ["sessionid", "some-other-cookie"]
    }

How does it work?
-----------------

``django-ultracache`` monkey patches
``django.template.base.Variable._resolve_lookup`` and
``django.db.models.Model.__getattribute__`` to make a record of model objects
as they are resolved. The ``ultracache`` template tag, ``ultracache`` decorator
and ``ultracache`` context manager inspect the list of objects contained
within them and keep a registry in Django's caching backend. A ``post_save``
signal handler monitors objects for changes and expires the appropriate cache
keys.

Tips
----

#. If you are running a cluster of Django nodes then ensure that they use a shared caching backend.

