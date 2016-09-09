from django.conf import settings
from django.core.exceptions import PermissionDenied

def lcms_only(view_func):
    def authorize(request, *args, **kwargs):
        user_ip = request.META['REMOTE_ADDR']
        if not getattr(settings, 'DEFY_LCMS_IP') or settings.DEFY_LCMS_IP == user_ip:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return authorize

def defy_token_required(view_func):
    def authorize(request, *args, **kwargs):
        auth_token = request.META.get('HTTP_X_TOKEN')
        permit = (auth_token is not None and auth_token in settings.DEFY_AUTH_TOKENS)
        if not permit:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return authorize

