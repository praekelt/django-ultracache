import copy
import json

from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings

from rest_framework.test import APIRequestFactory, APIClient

from ultracache.tests.models import DummyModel
from ultracache.tests.viewsets import DummyViewSet


class DRFTestCase(TestCase):
    fixtures = ["sites.json"]

    @classmethod
    def setUpTestData(cls):
        super(DRFTestCase, cls).setUpTestData()

        cls.user_model = get_user_model()

        # Superuser
        cls.superuser = cls.user_model.objects.create(
            username="superuser",
            email="superuser@test.com",
            is_superuser=True,
            is_staff=True
        )
        cls.superuser.set_password("password")
        cls.superuser.save()

        # Staff
        cls.staff = cls.user_model.objects.create(
            username="staff",
            email="staff@test.com",
            is_staff=True
        )
        cls.staff.set_password("password")
        cls.staff.save()

        # Plain user
        cls.user = cls.user_model.objects.create(
            username="user",
            email="user@test.com"
        )
        cls.user.set_password("password")
        cls.user.save()

    def setUp(self):
        super(DRFTestCase, self).setUp()
        self.factory = APIRequestFactory()
        self.client = APIClient()
        self.client.logout()
        self.one = DummyModel.objects.create(title="One", code="one")
        self.two = DummyModel.objects.create(title="Two", code="two")

    def tearDown(self):
        self.client.logout()
        DummyModel.objects.all().delete()
        super(DRFTestCase, self).tearDown()

    def test_get_dummymodels(self):
        response = self.client.get("/api/dummies/")
        as_json_1 = json.loads(response.content)

        # Drop to low level API so post_save does not trigger, meaning the
        # cached version is fetched on the next request.
        DummyModel.objects.filter(pk=self.one.pk).update(title="Onae")
        response = self.client.get("/api/dummies/")
        as_json_2 = json.loads(response.content)
        self.assertEqual(as_json_1, as_json_2)

        # Modify it the normal way, which removes the item from cache.
        self.one.title = "Onbe"
        self.one.save()
        response = self.client.get("/api/dummies/")
        as_json_3 = json.loads(response.content)
        self.assertNotEqual(as_json_1, as_json_3)

        # Trivial fetch to prove it is cached now
        response = self.client.get("/api/dummies/")
        as_json_4 = json.loads(response.content)
        self.assertEqual(as_json_3, as_json_4)

        # Modify via API to confirm that post_save is fired implicitly
        data = {
            "title": "Onze"
        }
        response = self.client.patch("/api/dummies/%s/" % self.one.pk, data)
        response = self.client.get("/api/dummies/")
        as_json_5 = json.loads(response.content)
        self.assertNotEqual(as_json_4, as_json_5)

        # Add an evaluate parameter which leads to a cache miss. Also
        # surreptiously edit the object so we can confirm a cache miss.
        DummyModel.objects.filter(pk=self.one.pk).update(title="Once")
        di = copy.deepcopy(settings.ULTRACACHE)
        di["drf"] = {"viewsets": {"*": {"evaluate": "request.user.is_anonymous"}}}
        with override_settings(ULTRACACHE=di):
            response = self.client.get("/api/dummies/")
            as_json_6 = json.loads(response.content)
            self.assertNotEqual(as_json_5, as_json_6)

        # Trivial fetch to refresh the cache
        response = self.client.get("/api/dummies/")
        as_json_7 = json.loads(response.content)

        # Disable viewset caching which leads to a cache miss. Also
        # surreptiously edit the object so we can confirm a cache miss.
        DummyModel.objects.filter(pk=self.one.pk).update(title="Onde")
        di = copy.deepcopy(settings.ULTRACACHE)
        di["drf"] = {"viewsets": {object: {}}}
        with override_settings(ULTRACACHE=di):
            response = self.client.get("/api/dummies/")
            as_json_8 = json.loads(response.content)
            self.assertNotEqual(as_json_7, as_json_8)

        # Trivial fetch to refresh the cache
        response = self.client.get("/api/dummies/")
        as_json_9 = json.loads(response.content)

        # Enable viewset caching for a single viewset class. Also
        # surreptiously edit the object so we can confirm a cache hit.
        DummyModel.objects.filter(pk=self.one.pk).update(title="Onee")
        di = copy.deepcopy(settings.ULTRACACHE)
        di["drf"] = {"viewsets": {DummyViewSet: {}}}
        with override_settings(ULTRACACHE=di):
            response = self.client.get("/api/dummies/")
            as_json_10 = json.loads(response.content)
            self.assertEqual(as_json_9, as_json_10)

    def test_get_dummymodel(self):
        url = "/api/dummies/%s/" % self.one.pk
        response = self.client.get(url)
        as_json_1 = json.loads(response.content)

        # Drop to low level API so post_save does not trigger, meaning the
        # cached version is fetched on the next request.
        DummyModel.objects.filter(pk=self.one.pk).update(title="Onfe")
        response = self.client.get(url)
        as_json_2 = json.loads(response.content)
        self.assertEqual(as_json_1, as_json_2)

        # Modify it the normal way, which removes the item from cache.
        self.one.title = "Onge"
        self.one.save()
        response = self.client.get(url)
        as_json_3 = json.loads(response.content)
        self.assertNotEqual(as_json_1, as_json_3)
