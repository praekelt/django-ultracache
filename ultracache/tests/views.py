from django.core.cache import cache
from django.views.generic.base import TemplateView

from ultracache.decorators import cached_get, ultracache
from ultracache.tests.models import DummyModel, DummyForeignModel, \
    DummyOtherModel


class RenderView(TemplateView):
    """Simple view that renders a dummy model.
    """
    template_name = "ultracache/render_view.html"

    def get_context_data(self, **kwargs):
        context = super(RenderView, self).get_context_data(**kwargs)
        context["one"] = DummyModel.objects.get(code="one")
        try:
            context["four"] = DummyOtherModel.objects.get(code="four")
        except DummyOtherModel.DoesNotExist:
            pass
        try:
            context["five"] = DummyOtherModel.objects.get(code="five")
        except DummyOtherModel.DoesNotExist:
            pass
        return context


class BaseCachedView(TemplateView):
    template_name = "ultracache/cached_view.html"

    def get_context_data(self, **kwargs):
        context = super(BaseCachedView, self).get_context_data(**kwargs)
        context["one"] = DummyModel.objects.get(code="one")
        context["two"] = DummyModel.objects.get(code="two")
        context["three"] = DummyForeignModel.objects.get(code="three")
        context["four"] = DummyModel.objects.get(code="four")

        # The counter is used to track the iteration that a cached block was
        # last rendered. Setting the value on the cache is the easiest way to
        # influence the counter from a test.
        context["counter"] = cache.get("counter", 1)

        # We never actually do anything with five, but cached_get is aware of it
        dc = DummyModel.objects.get(code="five")

        return context


class MethodCachedView(BaseCachedView):

    @cached_get(300, "request.is_secure()", 456)
    def get(self, *args, **kwargs):
        return super(MethodCachedView, self).get(*args, **kwargs)


@ultracache(300, "request.is_secure()", 456)
class ClassCachedView(BaseCachedView):
    pass


class CachedHeaderView(TemplateView):
    template_name = "ultracache/cached_header_view.html"
    content_type = "application/json"

    @cached_get(300)
    def get(self, *args, **kwargs):
        response = super(CachedHeaderView, self).get(*args, **kwargs)
        response["foo"] = "bar"
        return response


class BustableCachedView(TemplateView):
    template_name = "ultracache/bustable_cached_view.html"

    @cached_get(300)
    def get(self, *args, **kwargs):
        return super(BustableCachedView, self).get(*args, **kwargs)


class NonBustableCachedView(TemplateView):
    template_name = "ultracache/non_bustable_cached_view.html"

    @cached_get(300, "request.path_info")
    def get(self, *args, **kwargs):
        return super(NonBustableCachedView, self).get(*args, **kwargs)
