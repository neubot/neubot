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

import shlex
import sys

def parse(path):
    ''' Parse configuration file '''
    conf = {}
    filep = open(path, 'rb')
    lineno = 0
    for line in filep:
        lineno += 1
        tokens = shlex.split(line, True)
        if not tokens:
            continue
        if len(tokens) != 2:
            sys.stderr.write('WARNING: utils_rc: %s:%d: Invalid line\n' % (
                             path, lineno))
            return {}
        name, value = tokens
        conf[name] = value
    return conf

def parse_safe(path):
    ''' Parse configuration file (safe) '''
    try:
        return parse(path)
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        exc = sys.exc_info()[1]
        error = str(exc)
        sys.stderr.write('WARNING: utils_rc: %s\n' % error)
        return {}

def main(args):
    ''' main() function '''
    for arg in args[1:]:
        print parse(arg)

if __name__ == '__main__':
    main(sys.argv)
