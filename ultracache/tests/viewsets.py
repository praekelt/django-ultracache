import django

from rest_framework import viewsets, serializers

from ultracache.tests.models import DummyModel


class DummySerializer(serializers.ModelSerializer):

    class Meta:
        model = DummyModel
        if not django.get_version().startswith("1.6"):
            fields = "__all__"


class DummyViewSet(viewsets.ModelViewSet):
    queryset = DummyModel.objects.all()
    serializer_class = DummySerializer
