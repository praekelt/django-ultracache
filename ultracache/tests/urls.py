from django.conf.urls import include, url

from rest_framework.routers import DefaultRouter

from ultracache.tests import views, viewsets


router = DefaultRouter()
router.register(r"dummies", viewsets.DummyViewSet)

urlpatterns = [
    url(r"^api/", include(router.urls)),
    url(
        r"^render-view/$",
        views.RenderView.as_view(),
        name="render-view"
    ),
    url(
        r"^method-cached-view/$",
        views.MethodCachedView.as_view(),
        name="method-cached-view"
    ),
    url(
        r"^class-cached-view/$",
        views.ClassCachedView.as_view(),
        name="class-cached-view"
    ),
    url(
        r"^cached-header-view/$",
        views.CachedHeaderView.as_view(),
        name="cached-header-view"
    ),
    url(
        r"^bustable-cached-view/$",
        views.BustableCachedView.as_view(),
        name="bustable-cached-view"
    ),
    url(
        r"^non-bustable-cached-view/$",
        views.NonBustableCachedView.as_view(),
        name="non-bustable-cached-view"
    ),
]
