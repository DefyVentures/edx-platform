import json

from django.http import HttpResponse
from django.contrib import auth

import branding
import courseware

from .decorators import lcms_only


class NormalizeData(object):

    SERIALIZABLE_TYPES = [str, int, bool, float, list, dict, type(None)]

    def __init__(self, element):
        self.element = element

    def execute(self):
        if isinstance(self.element, dict):
            self.iterate_dict()
        if isinstance(self.element, list):
            self.iterate_list()
        else:
            return

    def normalize(self, el):

        #if isinstance(el, <ClassName>):
        #    # Do custom serialization here
        #    return el

        # Check if the object has a `__norm()` function for custom normalization.
        if hasattr(el, '__norm'):
            return el.__norm()

        if type(el) not in self.SERIALIZABLE_TYPES:
            return unicode(el)
        return el

    def iterate_list(self):
        for i in range(len(self.element)):
            self.element[i] = self.normalize(self.element[i])
            node = NormalizeData(self.element[i])
            node.execute()

    def iterate_dict(self):
        for key in self.element:
            self.element[key] = self.normalize(self.element[key])
            node = NormalizeData(self.element[key])
            node.execute()

def dumps(data):
    """ JSON serialize any object.
    """
    norm = NormalizeData(data)
    norm.execute()
    try:
        return json.dumps(norm.element)
    except TypeError:
        return unicode(norm.element)

@lcms_only
def courses(request):
    """ Returns a json response with course data.
    """
    courses = []
    for course in branding.get_visible_courses():
        data = {
            'def_id': course.scope_ids.def_id,
            'org':    course.org,
            'number': course.number,
            'start':  course.start,
            'end':    course.end,
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
    return HttpResponse(dumps(courses), content_type='application/json')

def student_progress(request):
    """ Return a json response with student progress data.

    TODO: This will need to be modified at some point to only return a subset of data.  Perhaps
    it get's passed a datetime `since` and only returns data that's been modified since then.
    """

    # Make courses accessible by module_id in a dict
    courses = {}
    for course in branding.get_visible_courses():
        module_id = dumps(course.scope_ids.def_id)
        courses[module_id] = course

    data = []
    course_modules = courseware.models.StudentModule.objects.filter(module_type='course')
    for course_module in course_modules:

        # Get detailed user progress data
        module_id = dumps(course_module.module_state_key)
        course = courses[module_id]
        courseware.grades.progress_summary(course_module.student, request, course)

        total_problems = 0
        completed_problems = 0
        problem_modules = courseware.models.StudentModule.objects.filter(
            module_type='problem',
            student=course_module.student,
            course_id=course_module.course_id,
        )
        for problem_module in problem_modules:
            state = json.loads(problem_module.state)
            total_problems += 1
            if state.get('done', False):
                completed_problems += 1

        data.append({
            'email':       course_module.student.email,
            'module_type': course_module.module_type,
            'module_id':   module_id,
            'state':       json.loads(course_module.state),
            'created':     course_module.created,
            'modified':    course_module.modified,
            'course_id':   course_module.course_id,
            'total_problems':     total_problems,
            'completed_problems': completed_problems,
        })

    return HttpResponse(dumps(data), content_type='application/json')

