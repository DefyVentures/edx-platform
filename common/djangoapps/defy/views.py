import json

from django.conf import settings
from django.contrib import auth
from django.http import HttpResponse, HttpResponseRedirect
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.csrf import csrf_exempt

import pymongo
import dateutil

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
            'problems': course_problems(course.org, course.number),
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

def course_problems(course_org, course_number):
    """ Return a list of ids for each problem in the given course.
    """
    db = pymongo.MongoClient().edxapp
    problems_cursor = db.modulestore.find({
        '_id.org': course_org,
        '_id.course': course_number,
        '_id.category': 'problem',
    })
    problems = []
    for problem in problems_cursor:
        data = {
            'name': problem['_id']['name'],
            'definition': problem['definition']['data']['data'],
        }
        problems.append(data)
    return problems

@csrf_exempt
@lcms_only
def student_progress(request):
    """ Return a json response with student progress data.

    TODO: This will need to be modified at some point to only return a subset of data.  Perhaps
    it get's passed a datetime `since` and only returns data that's been modified since then.
    """
    data = []
    problems = []

    since = request.POST.get('since')
    if since:
        since = dateutil.parser.parse(since)

    # Make courses accessible by module_id in a dict
    courses = {}
    for course in branding.get_visible_courses():
        module_id = dumps(course.scope_ids.def_id)
        courses[module_id] = course
    course_modules = courseware.models.StudentModule.objects.filter(module_type='course')

    for course_module in course_modules:

        # Get detailed user progress data
        module_id = dumps(course_module.module_state_key)
        course = courses.get(module_id)
        if not course:
            # Course no longer exists
            continue
        courseware.grades.progress_summary(course_module.student, request, course)

        modified = course_module.modified
        total_problems = 0
        completed_problems = 0
        grade = 0
        max_grade = 0
        problem_modules = courseware.models.StudentModule.objects.filter(
            module_type='problem',
            student=course_module.student,
            course_id=course_module.course_id,
        )
        if since:
            problem_modules = problem_modules.filter(modified__gte=since)
        for problem_module in problem_modules:
            state = json.loads(problem_module.state)
            problems.append({
                'email':      course_module.student.email,
                'course_id':  module_id,
                'problem_id': str(problem_module.module_state_key).split('/')[-1],
                'attempts':   state.get('attempts', 0),
                'done':       state.get('done') is True,
                'grade':      problem_module.grade,
                'max_grade':  problem_module.max_grade,
                'modified':   problem_module.modified,
            })

    return HttpResponse(dumps(problems), content_type='application/json')


@ensure_csrf_cookie
def logout_user(request):
    """ Log the user out and redirect them to Defy LCMS logout.
    """
    auth.logout(request)
    response = HttpResponseRedirect(settings.DEFY_LCMS_BASE_URL + '/logout')
    response.delete_cookie(
        settings.EDXMKTG_COOKIE_NAME,
        path='/', domain=settings.SESSION_COOKIE_DOMAIN,
    )
    return response

