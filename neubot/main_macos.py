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
import logging
import os
import subprocess
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot import log
from neubot import main_common
from neubot import utils_ctl
from neubot import utils_version

def subcommand_start(args):
    ''' Start subcommand '''

    try:
        options, arguments = getopt.getopt(args[1:], 'adv')
    except getopt.error:
        sys.exit('usage: neubot start [-adv]')
    if arguments:
        sys.exit('usage: neubot start [-adv]')

    args = '-d'
    debug = 0
    for opt in options:
        if opt[0] == '-a':
            args += 'a'
        elif opt[0] == '-d':
            debug = 1
        elif opt[0] == '-v':
            log.set_verbose()
            args += 'v'

    if os.getuid() != 0 and os.geteuid() != 0:
        sys.exit('ERROR: must be root')

    if debug:
        import neubot.updater.unix
        sys.argv = ['neubot updater_unix', args]
        logging.debug('main_macos: about to run: %s', str(sys.argv))
        neubot.updater.unix.main()
        sys.exit(1)  # should not happen

    cmdline = ['/bin/launchctl', 'start', 'org.neubot']
    logging.debug('main_macos: about to exec: %s', str(cmdline))
    retval = subprocess.call(cmdline)
    logging.debug('main_macos: return value: %d', retval)
    sys.exit(retval)

def subcommand_status(args):
    ''' Status subcommand '''

    try:
        options, arguments = getopt.getopt(args[1:], 'v')
    except getopt.error:
        sys.exit('usage: neubot status [-v]')
    if arguments:
        sys.exit('usage: neubot status [-v]')

    for opt in options:
        if opt[0] == '-v':
            log.set_verbose()

    running = utils_ctl.is_running('127.0.0.1', '9774', log.is_verbose())
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

    for opt in options:
        if opt[0] == '-v':
            log.set_verbose()

    if os.getuid() != 0 and os.geteuid() != 0:
        sys.exit('ERROR: must be root')

    cmdline = ['/bin/launchctl', 'stop', 'org.neubot']
    logging.debug('main_macos: about to exec: %s', str(cmdline))
    retval = subprocess.call(cmdline)
    logging.debug('main_macos: return value: %d', retval)
    sys.exit(retval)

USAGE = '''\
usage: neubot -h|--help
       neubot -V
       neubot start [-dv]
       neubot status [-v]
       neubot stop [-v]
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
