# neubot/utils_main.py

#
# Copyright (c) 2011 Roberto D'Auria <everlastingfire@autistici.org>
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

''' Run a subcommand's main() '''

import sys
import logging

if __name__ == '__main__':
    sys.path.insert(0, '.')

def main(args):
    ''' Run a subcommand's main() '''

    # Args[0] must be the subcommand name
    subcommand = args[0]

    # Users are not supposed to prefix commands with 'neubot.'
    subcommand = 'neubot.' + subcommand

    # Dinamically load the selected subcommand's main() at runtime
    __import__(subcommand)
    mainfunc = sys.modules[subcommand].main

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

if __name__ == "__main__":
    # First argument must be module name
    del sys.argv[0]
    main(sys.argv)
