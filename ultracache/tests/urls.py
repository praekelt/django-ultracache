from django.conf.urls import patterns, include, url

from ultracache.tests import views


urlpatterns = patterns(
    '',
    url(
        r'^aview/$',
        views.AView.as_view(),
        name='aview'
    )
)
