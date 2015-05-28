import json

from django.http import HttpResponse
from django.contrib import auth

import branding
import courseware

from .decorators import lcms_only

def dumps(value):
    """ Prepare value for JSON serialization.
    """
    if value is not None:
        return str(value)
    return value

@lcms_only
def courses(request):
    """ Returns a json response with course data.
    """
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
        data['about'] = {key: courseware.courses.get_course_about_section(course, key) for key in about_keys}
        courses.append(data)
    return HttpResponse(json.dumps(courses), content_type='application/json')

def student_progress(request):
    """ Return a json response with student progress data.
    """
    data = []
    modules = courseware.models.StudentModule.objects.filter(module_type='course')
    for module in modules:
        data.append({
            'email':       module.student.email,
            'module_type': module.module_type,
            'module_id':   dumps(module.module_state_key),
            'state':       json.loads(module.state),
            'created':     dumps(module.created),
            'modified':    dumps(module.modified),
            'course_id':   dumps(module.course_id),
        })
    return HttpResponse(json.dumps(data), content_type='application/json')

