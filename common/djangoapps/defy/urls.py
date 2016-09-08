from django.conf.urls import include, patterns, url

# /apidefy/
urlpatterns = patterns(
    'defy.views',
    url(r'^courses$', 'courses'),
    url(r'^student/progress$', 'student_progress'),
    url(r'^logout$', 'logout_user'),
    url(r'^account_info$', 'account_info'),
)

