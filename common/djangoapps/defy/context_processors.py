import re

from django.conf import settings
from django.core.cache import cache

import requests

def _key(key, email):
    """ Return the key used to cache a Defy html block.

    Append the email for nav blocks since that's the only block that will change depending on the
    user.
    """
    key = 'DEFY_' + key.upper()
    if key == 'DEFY_NAV':
        return key + ':' + email
    return key

def _massage_html(html):
    return html.replace('="/', '="{0}/'.format(settings.DEFY_LCMS_BASE_URL))

def _defy_blocks(email):
    """ Fetches a basic Defy dashboard and returns a dict of blocks to be inserted in edX
    templates.
    """
    url = settings.DEFY_LCMS_BASE_URL + '/accounts/dashboard'
    r = requests.get(url, params={'email': email})
    html_parts = r.text.split('<!--defylcms-')
    re_part = re.compile('start:(\w+)-->')
    ctx = {}
    for html_part in html_parts:
        match = re_part.match(html_part)
        if not match:
            continue
        key = match.group(1)
        value = html_part.replace(match.group(0), '', 1)
        ctx[_key(key, email)] = _massage_html(value)
    return ctx

def theme(request):
    """ Defines template variables used to render the Defy header and footer.
    """

    VAR_NAMES = ['NAV', 'FOOTER', 'STYLES']

    if not request.user.is_authenticated():
        return {}

    email = request.user.email
    var_names = [_key(name, email) for name in VAR_NAMES]
    ctx = cache.get_many(var_names)
    for name in var_names:
        if name not in ctx:
            ctx = _defy_blocks(email)
            cache.set_many(ctx, settings.DEFY_CACHE_SECONDS)
            break

    replace_key = _key('NAV', email)
    ctx['DEFY_NAV'] = ctx.pop(_key('NAV', email))

    ctx['IS_DEFY_ENABLED'] = True
    return ctx

