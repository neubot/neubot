# neubot/utils_rc.py

#
# Copyright (c) 2012 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Neubot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Neubot.  If not, see <http://www.gnu.org/licenses/>.
#

''' Configuration file utils '''

import getopt
import os
import pprint
import shlex
import sys

def parse(path=None, iterable=None):
    ''' Parse configuration file or iterable '''

    if path and iterable:
        raise ValueError('Both path and iterable are not None')
    elif path:
        if not os.path.isfile(path):
            return {}
        iterable = open(path, 'rb')
    elif iterable:
        path = '<cmdline>'
    else:
        return {}

    conf = {}
    lineno = 0
    for line in iterable:
        lineno += 1
        tokens = shlex.split(line, True)
        if not tokens:
            continue

        # Support both key=value and 'key value' syntaxes
        if len(tokens) == 1 and '=' in tokens[0]:
            tokens = tokens[0].split('=', 1)
        if len(tokens) != 2:
            raise ValueError('%s:%d: Invalid line' % (path, lineno))

        name, value = tokens
        conf[name] = value

    return conf

def parse_safe(path=None, iterable=None):
    ''' Parse configuration file or iterable (safe) '''
    try:
        return parse(path, iterable)
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        exc = sys.exc_info()[1]
        error = str(exc)
        sys.stderr.write('WARNING: utils_rc: %s\n' % error)
        return {}

def main(args):
    ''' main() function '''

    try:
        options, arguments = getopt.getopt(args[1:], 'f:O:')
    except getopt.error:
        sys.exit('usage: neubot utils_rc [-f file] [-O setting]')
    if arguments:
        sys.exit('usage: neubot utils_rc [-f file] [-O setting]')

    path = None
    settings = []
    for name, value in options:
        if name == '-f':
            path = value
        elif name == '-O':
            settings.append(value)

    if path:
        result = parse_safe(path)
        pprint.pprint(result)

    if settings:
        result = parse_safe(iterable=settings)
        pprint.pprint(result)

if __name__ == '__main__':
    main(sys.argv)
