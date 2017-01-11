#!/usr/bin/env python

import json
import subprocess
import sys

data = json.load(sys.stdin)
for _find, _repl in data:
    print("Replacing \"{0}\" with \"{1}\"...".format(_find, _repl))
    subprocess.check_output([
        'mongo',
        'localhost:27017/edxapp',
        '--eval', 'var _find="{0}", _repl="{1}"'.format(_find, _repl),
        '/edx/app/edxapp/edx-platform/scripts/mongo-find-replace.js',
    ], stderr=subprocess.STDOUT)

