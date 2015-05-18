from django.conf.urls import include, patterns, url

urlpatterns = patterns(
    url(r'^$', 'defy.views.index'),
)

