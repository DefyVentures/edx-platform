import json

from django.http import HttpResponse

import branding
from courseware.courses import get_course_about_section

from .decorators import lcms_only

def dumps(value):
    """ Prepare value for JSON serialization.
    """
    if value is not None:
        return str(value)
    return value

@lcms_only
def courses(request):

    courses = []
    for course in branding.get_visible_courses():
        data = {
            'def_id': dumps(course.scope_ids.def_id),
            'org':    course.org,
            'number': course.number,
            'start':  dumps(course.start),
            'end':    dumps(course.end),
        }
        about_keys = [
            'overview',
            'title',
            'university',
            'number',
            'short_description',
            'description',
            'key_dates', # (includes start, end, exams, etc)
            'video',
            'course_staff_short',
            'course_staff_extended',
            'requirements',
            'syllabus',
            'textbook',
            'faq',
            'more_info',
            'ocw_links',
        ]
        data['about'] = {key: get_course_about_section(course, key) for key in about_keys}
        courses.append(data)

    return HttpResponse(json.dumps(courses), content_type='application/json')

