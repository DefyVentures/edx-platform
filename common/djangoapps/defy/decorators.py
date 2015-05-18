from django.conf import settings

def lcms_only(view_func):
    def authorize(request, *args, **kwargs):
        user_ip = request.META['REMOTE_ADDR']
        if user_ip in settings.DEFY_LCMS_IPS or len(settings.DEFY_LCMS_IPS) == 0:
            return view_func(request, *args, **kwargs)
        raise Http404
    return authorize

