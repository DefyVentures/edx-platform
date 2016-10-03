from django.conf.urls import include, patterns, url

# /apidefy/
urlpatterns = patterns(
    'defy.views',
    url(r'^courses$', 'courses'),
    url(r'^course_ids$', 'course_ids'),
    url(r'^student/progress$', 'student_progress'),
    url(r'^course_modules$', 'course_modules'),
    url(r'^logout$', 'logout_user'),
    url(r'^account_info$', 'account_info'),
)

