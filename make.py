#!/usr/bin/env python

import argparse
from os import environ
import socket
import subprocess
import sys
import json

from openedx import env

required_settings = [
    'GIT_BRANCH',
    'OAUTH2_BASE_URL',
    'DATABASE_HOST',
    'DATABASE_PASSWORD',
    'SOCIAL_AUTH_DEFYVENTURES_OAUTH2_KEY',
    'SOCIAL_AUTH_DEFYVENTURES_OAUTH2_SECRET',
    'STACK',
]

env_settings = {
    'production': {
        'GIT_BRANCH': 'defy/release',
        'OAUTH2_BASE_URL': 'http://learn.defyventures.org',
        'DATABASE_HOST': 'edxapp-prod.cwxas7opvqi4.us-east-1.rds.amazonaws.com',
        'STACK': 'full',
    },
    'qa': {
        'GIT_BRANCH': 'defy/master',
        'OAUTH2_BASE_URL': 'http://learn.defybox.org',
        'DATABASE_HOST': 'edxapp-qa.cwxas7opvqi4.us-east-1.rds.amazonaws.com',
        'STACK': 'full',
    },
    'local': {
        'GIT_BRANCH': 'defy/master',
        'OAUTH2_BASE_URL': 'http://learn.defy.org',
        'DATABASE_HOST': 'localhost',
        'STACK': 'dev',
    }
}

with open('/edx/app/edxapp/defy.env.json') as defy_env_fp:
    secret_settings = json.load(defy_env_fp)
env_name = secret_settings['ENV']
settings = env_settings[env_name]
settings.update(secret_settings)

missing_settings = [s for s in required_settings if s not in settings]
if len(missing_settings) > 0:
    raise AttributeError('Missing settings: ' + missing_settings.join(', '))

def run(cmd, show=False):
    if show:
        print(cmd)
    else:
        print(cmd)
        return_code = subprocess.call(cmd, shell=True)
        if return_code != 0:
            sys.stderr.write(cmd + ' FAILED\n')
        sys.stdout.flush()
        sys.stderr.flush()

def run_all(cmds, fast=False, show=False):
    for options in cmds:
        if 'stack' in options and options['stack'] != settings['STACK']:
            continue
        if fast and not options.get('fast', False):
            continue
        if type(options['cmd']) == str:
            run(options['cmd'], show=show)
        else:
            options['cmd']()

def write_config():
    server_vars = """
edx_platform_repo: "https://github.com/DefyVentures/edx-platform.git"
edx_platform_version: "{GIT_BRANCH}"

# Required by XBlock
EDXAPP_ALLOW_ALL_ADVANCED_COMPONENTS: true

# Settings for enabling and configuring third party authorization
EDXAPP_ENABLE_THIRD_PARTY_AUTH: true
EDXAPP_THIRD_PARTY_AUTH:
    DefyVentures:
        SOCIAL_AUTH_DEFYVENTURES_OAUTH2_BASE_URL: "{OAUTH2_BASE_URL}"
        SOCIAL_AUTH_DEFYVENTURES_OAUTH2_KEY: "{SOCIAL_AUTH_DEFYVENTURES_OAUTH2_KEY}"
        SOCIAL_AUTH_DEFYVENTURES_OAUTH2_SECRET: "{SOCIAL_AUTH_DEFYVENTURES_OAUTH2_SECRET}"

EDXAPP_DATABASES:
    default:
        ENGINE: "django.db.backends.mysql"
        HOST: "{DATABASE_HOST}"
        NAME: "edxapp"
        USER: "edxapp001"
        PASSWORD: "{DATABASE_PASSWORD}"
        PORT: 3306
    read_replica:
        ENGINE: "django.db.backends.mysql"
        HOST: "{DATABASE_HOST}"
        NAME: "edxapp"
        USER: "edxapp001"
        PASSWORD: "{DATABASE_PASSWORD}"
        PORT: 3306
"""
    server_vars = server_vars.format(**settings)
    with open('/edx/app/edx_ansible/server-vars.yml', 'w') as fp:
        fp.write(server_vars)

def build(fast=False, show=False):
    supervisor_group = 'all'
    if fast:
        supervisor_group = 'edxapp:'
    cmds = [
        {
            'cmd': "sudo -u edxapp find . -name '*.pyc' -delete",
            'fast': True,
        },
        {
            'cmd': 'sudo -u edxapp git pull origin {GIT_BRANCH}'.format(**settings),
            'fast': True,
        },
        {
            'cmd': write_config,
        },
        {
            'cmd': '/edx/bin/update edx-platform {GIT_BRANCH}'.format(**settings),
            'stack': 'full',
        },
        {
            'cmd': 'sudo /edx/bin/supervisorctl restart {0}'.format(supervisor_group),
            'fast': True,
            'stack': 'full',
        },
    ]
    run_all(cmds, fast=fast, show=show)

def main():
    parser = argparse.ArgumentParser(description='Developemnt and admin tasks for Defy LCMS.')
    parser.add_argument('--build', '-b', action='store_true',
        help='Install requirements compile static files based on your current environment.')
    parser.add_argument('--fast', action='store_true',
        help='Skip installing requirements and building static files.  (Mainly for when you just want to restart supervisor.)')
    parser.add_argument('--show', action='store_true',
        help='Just show the commands that would be run wihtout actually running them.')
    parser.add_argument('--force', action='store_true', help='Do not exit if linting fails.')
    args = parser.parse_args()

    if args.build:
        build(fast=args.fast, show=args.show)

if __name__ == '__main__':
    main()

