from django.conf.urls import patterns, include, url

from ultracache.tests import views


urlpatterns = patterns(
    '',
    url(
        r'^render-view/$',
        views.RenderView.as_view(),
        name='render-view'
    ),
    url(
        r'^cached-view/$',
        views.CachedView.as_view(),
        name='cached-view'
    ),
    url(
        r'^cached-header-view/$',
        views.CachedHeaderView.as_view(),
        name='cached-header-view'
    ),
    url(
        r'^bustable-cached-view/$',
        views.BustableCachedView.as_view(),
        name='bustable-cached-view'
    ),
    url(
        r'^non-bustable-cached-view/$',
        views.NonBustableCachedView.as_view(),
        name='non-bustable-cached-view'
    ),
)
