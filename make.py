#!/usr/bin/env python

import argparse
from os import environ
import socket
import subprocess
import sys
import json

GIT_BRANCH = 'defy/release'
STACK = 'full'
RESUME_WIZARD_GIT_BRANCH = 'release'
RESUME_WIZARD_DIR = '/edx/app/edxapp/ResumeWizard'

with open('/edx/app/edxapp/defy.env.json') as fp:
    secret_settings = json.load(fp)

if secret_settings['ENVIRONMENT_NAME'] == 'production':
    pass

if secret_settings['ENVIRONMENT_NAME'] == 'qa':
    GIT_BRANCH = 'defy/master'
    RESUME_WIZARD_GIT_BRANCH = 'master'

if secret_settings['ENVIRONMENT_NAME'] == 'local':
    GIT_BRANCH = 'defy/master'
    STACK = 'dev'
    RESUME_WIZARD_GIT_BRANCH = 'master'
    RESUME_WIZARD_DIR = '/edx/app/edxapp/themes/ResumeWizard'

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
        if 'stack' in options and options['stack'] != STACK:
            continue
        if fast and not options.get('fast', False):
            continue
        if type(options['cmd']) == str:
            run(options['cmd'], show=show)
        else:
            options['cmd']()

def build(fast=False, show=False):
    supervisor_group = 'all'
    if fast:
        supervisor_group = 'edxapp:'
    cmds = [
        {
            'cmd': "sudo -u edxapp find . -name '*.pyc' -delete",
            'fast': True,
        },
        #{
        #    'cmd': 'sudo -u edxapp git pull',
        #    'fast': True,
        #},
        #{
        #    'cmd': 'cd {0} && sudo -u edxapp git pull && cd -'.format(RESUME_WIZARD_DIR),
        #    'fast': True,
        #},
        {
            'cmd': 'cd {0} && sudo -u edxapp rsync -av --checksum --delete resumewizard/ /edx/app/edxapp/venvs/edxapp/lib/python2.7/site-packages/resumewizard/ && cd -'.format(RESUME_WIZARD_DIR),
            'fast': True,
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

