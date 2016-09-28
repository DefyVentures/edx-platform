import json

from django.conf import settings

import requests

def send_webhook(course_key, action, usage_key=None):
    """ Send a webhook to LCMS that an xblock was created, updated, or deleted.
    """
    try:
        org, number, run = str(course_key).split(':', 1)[1].split('+', 2)
    except ValueError:
        org, number, run = str(course_key).split('/')
    except IndexError:
        org, number, run = str(course_key).split('/')
    if usage_key is not None:
        usage_key = str(usage_key)
    data = {
        'course': {
            'key': str(course_key),
            'org': org,
            'number': number,
            'run': run,
        },
        'usage_key': usage_key,
        'action': action,
    }
    requests.post(settings.DEFY_LCMS_BASE_URL + '/defyedx/course_action', data=json.dumps(data),
        headers={'X-TOKEN': settings.DEFY_AUTH_TOKEN})

