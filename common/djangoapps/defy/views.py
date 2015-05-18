from django.http import HttpResponse

from .decorators import lcms_only

@lcms_only
def index(request):
    return HttpResponse('ok')

def hi(request):
    return HttpResponse('hi')
