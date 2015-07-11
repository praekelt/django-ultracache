from django.views.generic.base import TemplateView

from ultracache.decorators import cached_get
from ultracache.tests.models import DummyModel, DummyForeignModel


class RenderView(TemplateView):
    """Simple view that renders a dummy model.
    """
    template_name = "ultracache/render_view.html"

    def get_context_data(self, **kwargs):
        context = super(RenderView, self).get_context_data(**kwargs)
        context["obj"] = DummyModel.objects.get(code="one")
        return context


class CachedView(TemplateView):
    template_name = "ultracache/cached_view.html"

    @cached_get(300, "request.get_full_path()", 456)
    def get(self, *args, **kwargs):
        return super(CachedView, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CachedView, self).get_context_data(**kwargs)
        context["one"] = DummyModel.objects.get(code="one")
        context["two"] = DummyModel.objects.get(code="two")
        context["three"] = DummyForeignModel.objects.get(code="three")
        context["counter"] = 1
        return context
