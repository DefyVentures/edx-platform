from django.conf.urls import include, patterns, url

# /api/defy/
urlpatterns = patterns(
    'defy.views',
    url(r'^courses$', 'courses'),
    url(r'^student/progress$', 'student_progress'),
)

