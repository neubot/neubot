# neubot/main_common.py

#
# Copyright (c) 2011 Roberto D'Auria <everlastingfire@autistici.org>
# Copyright (c) 2011-2012 Simone Basso <bassosimone@gmail.com>,
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

''' Common main() code for running subcommands '''

import sys
import logging

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot import utils_modules

SUBCOMMANDS = {
    'bittorrent': 'neubot.bittorrent',
    'browser': 'neubot.browser',
    'database': 'neubot.database.main',
    'notifier': 'neubot.notifier',
    'privacy': 'neubot.privacy',
    'raw': 'neubot.raw',
    'speedtest': 'neubot.speedtest.client',
    'viewer': 'neubot.viewer',
}

def main(subcommand, args):
    ''' Run a subcommand's main() '''

    utils_modules.modprobe(None, "load_subcommand", SUBCOMMANDS)

    #
    # Map subcommand to module.  The possiblity of running internal subcommands
    # by prefixing 'neubot.' to the module name is (for now) undocumented, but
    # is here because it is helpful for debugging.
    #
    if subcommand.startswith('neubot.'):
        module = subcommand
    elif not subcommand in SUBCOMMANDS:
        sys.stderr.write('Invalid subcommand: %s\n' % subcommand)
        print_subcommands(sys.stderr)
        sys.exit(1)
    else:
        module = SUBCOMMANDS[subcommand]

    # Dinamically load the selected subcommand's main() at runtime
    __import__(module)
    mainfunc = sys.modules[module].main

    # Fix args[0]
    args[0] = 'neubot ' + subcommand

    # Run main()
    try:
        mainfunc(args)
    except KeyboardInterrupt:
        sys.exit(1)
    except SystemExit:
        raise
    except:
        logging.error('Exception', exc_info=1)
        sys.exit(1)

def print_subcommands(filep):
    ''' Print list of available subcommands '''
    filep.write('subcommands:')
    for subcommand in sorted(SUBCOMMANDS):
        filep.write(' %s' % subcommand)
    filep.write('\n')

if __name__ == '__main__':
    # First argument must be module name
    del sys.argv[0]
    main(sys.argv[0], sys.argv)
