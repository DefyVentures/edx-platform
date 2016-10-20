import json
import re

from django.conf import settings
from django.contrib import auth
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django_future.csrf import ensure_csrf_cookie
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

import pymongo
import dateutil

import branding
import courseware

from defy.decorators import defy_token_required

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

def json_response(data):
    return HttpResponse(dumps(data), content_type='application/json')

def dumps(data):
    """ JSON serialize any object.
    """
    norm = NormalizeData(data)
    norm.execute()
    try:
        return json.dumps(norm.element)
    except TypeError:
        return unicode(norm.element)

@defy_token_required
def course_ids(request):
    """ Returns a full list of course ids.
    """
    data = {
        'course_ids': [course.scope_ids.def_id for course in branding.get_visible_courses()],
    }
    return HttpResponse(dumps(data), content_type='application/json')

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

def _student_progress(request):
    """ Return a json response with student progress data.
    """
    data = []
    coursemods = []

    # Make courses accessible by module_id in a dict
    courses = {}
    for course in branding.get_visible_courses():
        module_id = dumps(course.scope_ids.def_id)
        courses[module_id] = course

    course_modules = courseware.models.StudentModule.objects.filter(module_type='course')

    # Get only course modules that have problems modified since `since`.
    since = request.GET.get('since')
    if since:
        since = dateutil.parser.parse(since)
        student_courses = {}
        student_problems = courseware.models.StudentModule.objects.filter(
            module_type='problem', modified__gte=since)
        if len(student_problems) == 0:
            return json_response([])
        for student_problem in student_problems:
            key = str(student_problem.student_id) + str(student_problem.course_id)
            student_courses[key] = {
                'student_id': student_problem.student_id,
                'course_id': student_problem.course_id,
            }
        student_course_Q = Q()
        for kwargs in student_courses.itervalues():
            student_course_Q = student_course_Q | Q(module_type='course', **kwargs)
        course_modules = courseware.models.StudentModule.objects.filter(student_course_Q).distinct()

    course_modules = course_modules.order_by('pk')

    starting_after = request.GET.get('starting_after')
    if starting_after:
        course_modules = course_modules.filter(pk__gt=starting_after)

    limit = int(request.GET.get('limit', '100'))
    if limit < 1 or limit > 100:
        limit = 100
    course_modules = course_modules[:limit]

    for course_module in course_modules:
        # Get detailed user progress data
        module_id = dumps(course_module.module_state_key)
        course = courses.get(module_id)

        coursemod = {
            'student_pk': course_module.student.pk,
            'email':      course_module.student.email,
            'course_id':  module_id,
            'pk':         course_module.pk,
            'problem_mods': [],
        }

        if not course:
            # Course no longer exists
            coursemods.append(coursemod)
            continue

        courseware.grades.progress_summary(course_module.student, request, course)

        total_problems = 0
        completed_problems = 0
        grade = 0
        max_grade = 0
        problem_modules = courseware.models.StudentModule.objects.filter(
            module_type='problem',
            student=course_module.student,
            course_id=course_module.course_id,
        )
        course_modified = None
        course_grade = 0
        course_max_grade = 0
        for problem_module in problem_modules:
            state = json.loads(problem_module.state)
            coursemod['problem_mods'].append({
                'email':      course_module.student.email,
                'course_id':  module_id,
                'problem_id': str(problem_module.module_state_key).split('/')[-1],
                'attempts':   state.get('attempts', 0),
                'done':       state.get('done') is True,
                'grade':      problem_module.grade,
                'max_grade':  problem_module.max_grade,
                'modified':   problem_module.modified,
                'state':      state,
            })
            if course_modified is None or course_modified < problem_module.modified:
                course_modified = problem_module.modified
            if problem_module.grade is not None:
                course_grade += problem_module.grade
                course_max_grade += problem_module.max_grade
        coursemod['modified'] = course_modified
        coursemod['grade'] = course_grade
        coursemod['max_grade'] = course_max_grade
        coursemods.append(coursemod)

    return json_response(coursemods)

@csrf_exempt
@lcms_only
def student_progress(request):
    return _student_progress(request)

@defy_token_required
def course_modules(request):
    return _student_progress(request)

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

@csrf_exempt
@defy_token_required
def change_email(request):
    user_pk = request.POST['user_pk']
    email = request.POST['email']
    user = get_object_or_404(auth.models.User, pk=user_pk)
    user.email = email
    user.username = re.sub('[^a-zA-Z0-9]', '', email.replace('@', 'AT'))
    user.save()
    return HttpResponse()

@lcms_only
def account_info(request):

    email = request.GET.get('email')
    user_id = request.GET.get('id')

    user = None
    if email:
        user = get_object_or_404(auth.models.User, email=email)
    if user_id:
        user = get_object_or_404(auth.models.User, pk=user_id)
    if not user:
        raise Http404

    attrs = [
        'date_joined',
        'email',
        'first_name',
        'id',
        'is_active',
        'is_staff',
        'is_superuser',
        'last_login',
        'last_name',
        'username',
    ]
    data = {attr: getattr(user, attr) for attr in attrs}
    return HttpResponse(dumps(data), content_type='application/json')

