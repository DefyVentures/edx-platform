from .aws import defyenv

DEFY_LCMS_BASE_URL = 'https://learn.defyventures.org'

# A list of client IPs that can access views decorated with @lcms_only
DEFY_LCMS_IP = '10.0.0.64'

# Time to cache the Defy LCMS header for instance
DEFY_CACHE_SECONDS = 60 * 5

DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.mysql',
        'HOST':     'edxapp-prod.cwxas7opvqi4.us-east-1.rds.amazonaws.com',
        'NAME':     'edxapp',
        'USER':     'edxapp001',
        'PASSWORD': defyenv('DATABASE_PASSWORD'),
        'PORT':     3306
    },
}

THIRD_PARTY_AUTH = {
    'DefyVentures': {
        'SOCIAL_AUTH_DEFYVENTURES_OAUTH2_KEY': defyenv('SOCIAL_AUTH_DEFYVENTURES_OAUTH2_KEY'),
        'SOCIAL_AUTH_DEFYVENTURES_OAUTH2_SECRET': defyenv('SOCIAL_AUTH_DEFYVENTURES_OAUTH2_SECRET'),
    }
}

