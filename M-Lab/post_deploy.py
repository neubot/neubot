#!/usr/bin/env python

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

''' Postprocess deploy log '''

import collections
import sys

def main():
    ''' main() function '''

    current = ''
    good = set()
    hosts = collections.defaultdict(list)
    for line in sys.stdin:
        line = line.strip()

        # An empty line separates two hosts logs
        if not line:
            current = ''
            continue

        # The first nonempty line starts with the host name
        if not current:
            current = line.split(':', 1)[0]
        hosts[current].append(line)

        if 'deploy result: 0' in line:
            good.add(current)

    bad = set(hosts.keys()) - good

    sys.stdout.write('OK hosts (%d):\n' % len(good))
    for host in good:
        sys.stdout.write('\t%s\n' % host)
    sys.stdout.write('\nProblematic hosts (%d):\n' % len(bad))
    for host in bad:
        sys.stdout.write('\t%s\n' % host)

    sys.stdout.write('\nProblematic hosts log follows:\n\n')
    for host in bad:
        for line in hosts[host]:
            sys.stdout.write('%s\n' % line)
        sys.stdout.write('\n')

if __name__ == '__main__':
    main()
