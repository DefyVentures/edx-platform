import json

from django.conf import settings

import requests

def xblock_action(usage_key, action):
    """ Send a webhook to LCMS that an xblock was created, updated, or deleted.
    """
    org, number, run = str(usage_key.course_key).split('/')
    data = {
        'course': {
            'org': org,
            'number': number,
            'run': run,
        },
        'usage_key': str(usage_key),
        'action': action,
    }
    requests.post(settings.DEFY_LCMS_BASE_URL + '/defyedx/xblock_action', data=json.dumps(data))

