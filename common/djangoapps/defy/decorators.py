from django.conf import settings
from django.http import Http404

def lcms_only(view_func):
    def authorize(request, *args, **kwargs):
        user_ip = request.META['REMOTE_ADDR']
        if not getattr(settings, 'DEFY_LCMS_IP') or settings.DEFY_LCMS_IPS == user_ip:
            return view_func(request, *args, **kwargs)
        raise Http404
    return authorize

