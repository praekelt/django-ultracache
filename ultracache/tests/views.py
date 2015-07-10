from django.views.generic.base import TemplateView

from ultracache.tests.models import DummyModel, DummyForeignModel


class AView(TemplateView):
    """Simple view that renders a dummy model.
    """
    template_name = "ultracache/aview.html"

    def get_context_data(self, **kwargs):
        context = super(AView, self).get_context_data(**kwargs)
        context["obj"] = DummyModel.objects.get(code="one")
        return context

