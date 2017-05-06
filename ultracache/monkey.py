"""Monkey patch template variable resolution so we can recognize which objects
are covered within a containing caching template tag. The patch is based on
Django 1.9 but is backwards compatible with 1.6."""

import inspect
import md5
import types
from collections import OrderedDict

from django.core.cache import cache
from django.db.models import Model
from django.template.base import Variable, VariableDoesNotExist
from django.template.context import BaseContext
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from ultracache.utils import cache_meta, get_current_site_pk

try:
    from django.template.base import logger
except ImportError:
    logger = None


def _my_resolve_lookup(self, context):
        """
        Performs resolution of a real variable (i.e. not a literal) against the
        given context.

        As indicated by the method's name, this method is an implementation
        detail and shouldn"t be called by external code. Use Variable.resolve()
        instead.
        """
        current = context
        try:  # catch-all for silent variable failures
            for bit in self.lookups:
                try:  # dictionary lookup
                    current = current[bit]
                    # ValueError/IndexError are for numpy.array lookup on
                    # numpy < 1.9 and 1.9+ respectively
                except (TypeError, AttributeError, KeyError, ValueError, IndexError):
                    try:  # attribute lookup
                        # Don"t return class attributes if the class is the context:
                        if isinstance(current, BaseContext) and getattr(type(current), bit):
                            raise AttributeError
                        current = getattr(current, bit)
                    except (TypeError, AttributeError) as e:
                        # Reraise an AttributeError raised by a @property
                        if (isinstance(e, AttributeError) and
                                not isinstance(current, BaseContext) and bit in dir(current)):
                            raise
                        try:  # list-index lookup
                            current = current[int(bit)]
                        except (IndexError,  # list index out of range
                                ValueError,  # invalid literal for int()
                                KeyError,    # current is a dict without `int(bit)` key
                                TypeError):  # unsubscriptable object
                            raise VariableDoesNotExist("Failed lookup for key "
                                                       "[%s] in %r",
                                                       (bit, current))  # missing attribute
                if callable(current):
                    if getattr(current, "do_not_call_in_templates", False):
                        pass
                    elif getattr(current, "alters_data", False):
                        try:
                            current = context.template.engine.string_if_invalid
                        except AttributeError:
                            current = settings.TEMPLATE_STRING_IF_INVALID
                    else:
                        try:  # method call (assuming no args required)
                            current = current()
                        except TypeError:
                            try:
                                inspect.getcallargs(current)
                            except TypeError:  # arguments *were* required
                                try:
                                    current = context.template.engine.string_if_invalid  # invalid method call
                                except AttributeError:
                                    current = settings.TEMPLATE_STRING_IF_INVALID
                            else:
                                raise
                elif isinstance(current, Model):
                    if ("request" in context) and hasattr(context["request"], "_ultracache"):
                        # get_for_model itself is cached
                        ct = ContentType.objects.get_for_model(current.__class__)
                        context["request"]._ultracache.append((ct.id, current.pk))

        except Exception as e:
            template_name = getattr(context, "template_name", None) or "unknown"
            if logger is not None:
                logger.debug(
                    "Exception while resolving variable \"%s\" in template \"%s\".",
                    bit,
                    template_name,
                    exc_info=True,
                )

            if getattr(e, "silent_variable_failure", False):
                try:
                    current = context.template.engine.string_if_invalid
                except AttributeError:
                    current = settings.TEMPLATE_STRING_IF_INVALID
            else:
                raise

        return current

Variable._resolve_lookup = _my_resolve_lookup



"""If Django Rest Framework is installed patch a few mixins. Serializers are
conceptually the same as templates but make it even easier to track objects."""
try:
    from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
    from rest_framework.response import Response
    HAS_DRF = True
except ImportError:
    HAS_DRF = False


def drf_decorator(func):

    def wrapped(context, request, *args, **kwargs):
        viewsets = settings.ULTRACACHE.get("drf", {}).get("viewsets", {})
        do_cache =  (context.__class__ in viewsets) or ("*" in viewsets)

        if do_cache:
            li = [request.get_full_path()]
            viewset_settings = viewsets.get(context.__class__, {}) \
                or viewsets.get("*", {})
            evaluate = viewset_settings.get("evaluate", None)
            if evaluate is not None:
                li.append(eval(evaluate))

            if "django.contrib.sites" in settings.INSTALLED_APPS:
                li.append(get_current_site_pk(request))

            cache_key = md5.new(":".join([str(l) for l in li])).hexdigest()

            cached_response = cache.get(cache_key, None)
            if cached_response is not None:
                return cached_response

        obj_or_queryset, response = func(context, request, *args, **kwargs)

        if do_cache:
            if not hasattr(request, "_ultracache"):
                setattr(request, "_ultracache", [])
                setattr(request, "_ultracache_cache_key_range", [])

            try:
                iter(obj_or_queryset)
            except TypeError:
                obj_or_queryset = [obj_or_queryset]

            for obj in obj_or_queryset:
                # get_for_model itself is cached
                ct = ContentType.objects.get_for_model(obj.__class__)
                request._ultracache.append((ct.id, obj.pk))

            cache_meta(request, cache_key)

            response = context.finalize_response(request, response, *args, **kwargs)
            response.render()
            evaluate = viewset_settings.get("timeout", 300)
            cache.set(cache_key, response, 300)
            return response

        else:
            return response

    return wrapped


def mylist(self, request, *args, **kwargs):
    queryset = self.filter_queryset(self.get_queryset())

    page = self.paginate_queryset(queryset)
    if page is not None:
        consider = page
        serializer = self.get_serializer(page, many=True)
        response = self.get_paginated_response(serializer.data)
    else:
        consider = queryset
        serializer = self.get_serializer(queryset, many=True)
        response = Response(serializer.data)

    return consider, response

mylist = drf_decorator(mylist)


def myretrieve(self, request, *args, **kwargs):
    instance = self.get_object()
    serializer = self.get_serializer(instance)
    return instance, Response(serializer.data)

myretrieve = drf_decorator(myretrieve)


if HAS_DRF:
    ListModelMixin.list = mylist
    RetrieveModelMixin.retrieve = myretrieve
