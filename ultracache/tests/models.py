from django.db import models


class DummyModel(models.Model):
    title = models.CharField(max_length=32)
    code = models.CharField(max_length=32)


class DummyForeignModel(models.Model):
    title = models.CharField(max_length=32)
    points_to = models.ForeignKey(DummyModel)
    code = models.CharField(max_length=32)


class DummyOtherModel(models.Model):
    title = models.CharField(max_length=32)
    code = models.CharField(max_length=32)
