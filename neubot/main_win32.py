# neubot/main_win32.py

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

''' Win32 main() '''

import getopt
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot import main_common
from neubot import utils_ctl
from neubot import utils_version

# Reference viewer and notifier so py2exe includes 'em
if sys.platform == 'win32' and not hasattr(sys, 'frozen'):
    from neubot import notifier
    from neubot import raw
    from neubot import viewer

def subcommand_start(args):
    ''' Start subcommand '''

    try:
        options, arguments = getopt.getopt(args[1:], 'k')
    except getopt.error:
        sys.exit('usage: neubot start [-k]')
    if arguments:
        sys.exit('usage: neubot start [-k]')

    kill = False
    for tpl in options:
        if tpl[0] == '-k':
            kill = True

    #
    # Wait for the parent to die, so that it closes the listening
    # socket and we can successfully bind() it.
    #
    count = 0
    while kill:
        running = utils_ctl.is_running('127.0.0.1', '9774', quick=1)
        if not running:
            break
        utils_ctl.stop('127.0.0.1', '9774')
        count += 1
        if count > 512:
            sys.exit('FATAL: cannot stop neubot daemon')

    # Lazy import
    from neubot import background_win32
    background_win32.main(['neubot'])

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

    running = utils_ctl.is_running('127.0.0.1', '9774')
    if verbose:
        if not running:
            sys.stdout.write('Neubot is not running\n')
        else:
            sys.stdout.write('Neubot is running\n')
    if not running:
        sys.exit(1)

def subcommand_stop(args):
    ''' Stop subcommand '''

    try:
        options, arguments = getopt.getopt(args[1:], '')
    except getopt.error:
        sys.exit('usage: neubot stop')
    if options or arguments:
        sys.exit('usage: neubot stop')

    running = utils_ctl.is_running('127.0.0.1', '9774')
    if not running:
        sys.exit('ERROR: neubot is not running')

    utils_ctl.stop('127.0.0.1', '9774')

USAGE = '''\
usage: neubot -h|--help
       neubot -V
       neubot start [-k]
       neubot status [-v]
       neubot stop
       neubot subcommand [option]... [argument]...
'''

def main(args):
    ''' Main function '''

    if len(args) == 1:
        sys.stdout.write(USAGE)
        main_common.print_subcommands(sys.stdout)
        sys.exit(0)

    del args[0]
    subcommand = args[0]

    if subcommand == '--help' or subcommand == '-h':
        sys.stdout.write(USAGE)
        main_common.print_subcommands(sys.stdout)
        sys.exit(0)

    if subcommand == '-V':
        sys.stdout.write(utils_version.PRODUCT + '\n')
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

    main_common.main(subcommand, args)

if __name__ == '__main__':
    main(sys.argv)
