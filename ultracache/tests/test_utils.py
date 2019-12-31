from django.conf import settings
from django.core.cache import cache
from django.test import TestCase

from ultracache import _thread_locals
from ultracache.utils import Ultracache
from ultracache.tests.models import DummyModel


class UtilsTestCase(TestCase):
    if "django.contrib.sites" in settings.INSTALLED_APPS:
        fixtures = ["sites.json"]

    def setUp(self):
        super(UtilsTestCase, self).setUp()
        cache.clear()

    def test_context_manager_like_thing(self):
        one = DummyModel.objects.create(title="One", code="one")
        two = DummyModel.objects.create(title="Two", code="two")

        # Caching with object one
        uc = Ultracache(3600, "a", "b")
        self.failIf(uc)
        uc.cache(one.title)

        uc = Ultracache(3600, "a", "b")
        self.failUnless(uc)
        self.assertEqual(uc.cached, one.title)

        one.title = "Onex"
        one.save()

        uc = Ultracache(3600, "a", "b")
        self.failIf(uc)

        # Caching with object two. Ensure object one doesn't bleed into this
        # section.
        uc = Ultracache(3600, "c", "d")
        self.failIf(uc)
        uc.cache(two.title)

        uc = Ultracache(3600, "c", "d")
        self.failUnless(uc)
        self.assertEqual(uc.cached, two.title)

        two.title = "Onez"
        one.save()
        uc = Ultracache(3600, "c", "d")
        self.failUnless(uc)

        two.title = "Twox"
        two.save()

        uc = Ultracache(3600, "c", "d")
        self.failIf(uc)
