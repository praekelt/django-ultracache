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
    )
)
