from django.conf.urls import include, patterns, url

# /api/defy/
urlpatterns = patterns(
    'defy.views',
    url(r'^$', 'index'),
    url(r'^hi$', 'hi'),
)

