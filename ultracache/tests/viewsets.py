from rest_framework import viewsets, serializers

from ultracache.tests.models import DummyModel


class DummySerializer(serializers.ModelSerializer):

    class Meta:
        model = DummyModel


class DummyViewSet(viewsets.ModelViewSet):
    queryset = DummyModel.objects.all()
    serializer_class = DummySerializer
