"""Monkey patch template variable resolution so we can recognize which objects
are covered within a containing caching template tag. The patch is based on
Django 1.9 but is backwards compatible with 1.6."""

from django.template.base import Variable, VariableDoesNotExist
from django.template.context import BaseContext
from django.db.models import Model
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

try:
    from django.template.base import logger
except ImportError:
    logger = None


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
                    # ValueError/IndexError are for numpy.array lookup on
                    # numpy < 1.9 and 1.9+ respectively
                except (TypeError, AttributeError, KeyError, ValueError, IndexError):
                    try:  # attribute lookup
                        # Don't return class attributes if the class is the context:
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
                    if getattr(current, 'do_not_call_in_templates', False):
                        pass
                    elif getattr(current, 'alters_data', False):
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
                    if ('request' in context) and hasattr(context['request'], '_ultracache'):
                        # get_for_model itself is cached
                        ct = ContentType.objects.get_for_model(current.__class__)
                        context['request']._ultracache.append((ct.id, current.pk))

        except Exception as e:
            template_name = getattr(context, 'template_name', None) or 'unknown'
            if logger is not None:
                logger.debug(
                    "Exception while resolving variable '%s' in template '%s'.",
                    bit,
                    template_name,
                    exc_info=True,
                )

            if getattr(e, 'silent_variable_failure', False):
                try:
                    current = context.template.engine.string_if_invalid
                except AttributeError:
                    current = settings.TEMPLATE_STRING_IF_INVALID
            else:
                raise

        return current

Variable._resolve_lookup = _my_resolve_lookup
