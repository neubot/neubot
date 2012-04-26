# neubot/main_macos.py

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

''' MacOS main() '''

import getopt
import os
import subprocess
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot import utils_ctl

def subcommand_start(args):
    ''' Start subcommand '''

    try:
        options, arguments = getopt.getopt(args[1:], 'v')
    except getopt.error:
        sys.exit('usage: neubot start [-v]')
    if arguments:
        sys.exit('usage: neubot start [-v]')

    verbose = 0
    for opt in options:
        if opt[0] == '-v':
            verbose = 1

    if os.getuid() != 0 and os.geteuid() != 0:
        sys.exit('ERROR: must be root')

    cmdline = ['/bin/launchctl', 'start', 'org.neubot']
    if verbose:
        sys.stderr.write('DEBUG: about to exec: %s\n' % str(cmdline))
    retval = subprocess.call(cmdline)
    if verbose:
        sys.stderr.write('DEBUG: return value: %d\n' % retval)
    sys.exit(retval)

def subcommand_status(args):
    ''' Status subcommand '''

    try:
        options, arguments = getopt.getopt(args[1:], 'v')
    except getopt.error:
        sys.exit('usage: neubot status [-v]')
    if arguments:
        sys.exit('usage: neubot status [-v]')

    verbose = 0
    for opt in options:
        if opt[0] == '-v':
            verbose = 1

    running = utils_ctl.is_running('127.0.0.1', '9774', verbose)
    if not running:
        sys.exit('ERROR: neubot is not running')

def subcommand_stop(args):
    ''' Stop subcommand '''

    try:
        options, arguments = getopt.getopt(args[1:], 'v')
    except getopt.error:
        sys.exit('usage: neubot stop [-v]')
    if arguments:
        sys.exit('usage: neubot stop [-v]')

    verbose = 0
    for opt in options:
        if opt[0] == '-v':
            verbose = 1

    if os.getuid() != 0 and os.geteuid() != 0:
        sys.exit('ERROR: must be root')

    cmdline = ['/bin/launchctl', 'stop', 'org.neubot']
    if verbose:
        sys.stderr.write('DEBUG: about to exec: %s\n' % str(cmdline))
    retval = subprocess.call(cmdline)
    if verbose:
        sys.stderr.write('DEBUG: return value: %d\n' % retval)
    sys.exit(retval)

USAGE = '''\
usage: neubot -h|--help
       neubot -V
       neubot start [-v]
       neubot status [-v]
       neubot stop [-v]
       neubot subcommand [option]... [argument]...
'''

def main(args):
    ''' Main function '''

    if len(args) == 1:
        sys.stdout.write(USAGE)
        sys.exit(0)

    del args[0]
    subcommand = args[0]

    if subcommand == '--help' or subcommand == '-h':
        sys.stdout.write(USAGE)
        sys.exit(0)

    if subcommand == '-V':
        sys.stdout.write('Neubot 0.4.11\n')
        sys.exit(0)

    if subcommand == 'start':
        subcommand_start(args)
        sys.exit(0)

    if subcommand == 'status':
        subcommand_status(args)
        sys.exit(0)

    if subcommand == 'stop':
        subcommand_stop(args)
        sys.exit(0)

    # Special case
    if subcommand == 'database':
        # Lazy import
        import neubot.database.main
        neubot.database.main.main(args)
        sys.exit(0)

    # Lazy import
    from neubot import utils_module
    utils_module.main(args)

if __name__ == '__main__':
    main(sys.argv)
