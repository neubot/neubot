#!/usr/bin/env python

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
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

''' Emulates OpenBSD `cksum -a` functionality '''

import getopt
import hashlib
import sys
import traceback

def cksum_path(path, aarg):
    ''' Computes cksum of a given path '''
    cksum = hashlib.new(aarg)
    filep = open(path, 'rb')
    cksum.update(filep.read())
    return '%s  %s\n' % (cksum.hexdigest(), path)

def main():
    ''' Main function '''
    try:
        aarg = "sha1"
        options, arguments = getopt.getopt(sys.argv[1:], "a:")
        for key, value in options:
            if key == "-a":
                aarg = value

        for path in arguments:
            sys.stdout.write(cksum_path(path, aarg))

    except KeyboardInterrupt:
        sys.stderr.write('Interrupt\n')
        sys.exit(0)
    except:
        traceback.print_exc()
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
