from django.db import models


class DummyModel(models.Model):
    title = models.CharField(max_length=32)
    code = models.CharField(max_length=32)
models.register_models('ultracache', DummyModel)


class DummyForeignModel(models.Model):
    title = models.CharField(max_length=32)
    points_to = models.ForeignKey(DummyModel)
    code = models.CharField(max_length=32)
models.register_models('ultracache', DummyForeignModel)


class DummyOtherModel(models.Model):
    title = models.CharField(max_length=32)
    code = models.CharField(max_length=32)
models.register_models('ultracache', DummyOtherModel)
