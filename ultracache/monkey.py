"""Monkey patch template variable resolution so we can recognize which objects
are covered within a containing caching template tag."""

from django.template.base import Variable, VariableDoesNotExist
from django.template.context import BaseContext
from django.db.models import Model
from django.contrib.contenttypes.models import ContentType
from django.conf import settings


def _my_resolve_lookup(self, context):
        """
        Performs resolution of a real variable (i.e. not a literal) against the
        given context.

        As indicated by the method's name, this method is an implementation
        detail and shouldn't be called by external code. Use Variable.resolve()
        instead.
        """
        current = context
        try:  # catch-all for silent variable failures
            for bit in self.lookups:
                try:  # dictionary lookup
                    current = current[bit]
                except (TypeError, AttributeError, KeyError, ValueError):
                    try:  # attribute lookup
                        # Don't return class attributes if the class is the context:
                        if isinstance(current, BaseContext) and getattr(type(current), bit):
                            raise AttributeError
                        current = getattr(current, bit)
                    except (TypeError, AttributeError):
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
                    if getattr(current, 'do_not_call_in_templates', False):
                        pass
                    elif getattr(current, 'alters_data', False):
                        current = settings.TEMPLATE_STRING_IF_INVALID
                    else:
                        try: # method call (assuming no args required)
                            current = current()
                        except TypeError: # arguments *were* required
                            # GOTCHA: This will also catch any TypeError
                            # raised in the function itself.
                            current = settings.TEMPLATE_STRING_IF_INVALID  # invalid method call
                elif isinstance(current, Model):
                    if ('request' in context) and hasattr(context['request'], '_ultracache'):
                        # get_for_model itself is cached
                        ct = ContentType.objects.get_for_model(current.__class__)
                        context['request']._ultracache.append((ct.id, current.pk))

        except Exception as e:
            if getattr(e, 'silent_variable_failure', False):
                current = settings.TEMPLATE_STRING_IF_INVALID
            else:
                raise

        return current

Variable._resolve_lookup = _my_resolve_lookup
